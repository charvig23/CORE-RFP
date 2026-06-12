from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.orm import Session
from database import SessionLocal
from models import RFP, AgentExecution
from schemas import RFPCreate, RFPResponse, OrchestrationRequest
from services.orchestrator import AgentOrchestrator
from typing import List
import os

router = APIRouter(prefix="/rfp", tags=["RFP"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload", response_model=RFPResponse)
def upload_rfp(rfp: RFPCreate, db: Session = Depends(get_db)):
    """Upload RFP content for processing"""
    record = RFP(title=rfp.title, content=rfp.content, status="uploaded")
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.post("/upload-file")
async def upload_rfp_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload RFP as PDF/text file"""
    # Save file
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Extract text based on file type
    text_content = ""
    if file.filename.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
    elif file.filename.endswith('.pdf'):
        # Extract text from PDF using PyMuPDF
        try:
            import fitz  # PyMuPDF
            print(f"[PDF] Opening PDF: {file_path}")
            pdf_document = fitz.open(file_path)
            print(f"[PDF] Document has {pdf_document.page_count} pages")
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                page_text = page.get_text()
                text_content += page_text
                print(f"[PDF] Extracted {len(page_text)} chars from page {page_num + 1}")
            
            pdf_document.close()
            print(f"[PDF] Total extracted: {len(text_content)} characters")
            
            if not text_content.strip():
                raise Exception("PDF appears to be empty or contains only images")
                
        except ImportError as e:
            error_msg = f"PyMuPDF not installed. Run: pip install PyMuPDF"
            print(f"[PDF ERROR] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        except Exception as e:
            error_msg = f"Error extracting PDF: {str(e)}"
            print(f"[PDF ERROR] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
    else:
        text_content = f"File uploaded: {file.filename}. Unsupported format for text extraction."
    
    record = RFP(
        title=file.filename,
        content=text_content,
        file_path=file_path,
        status="uploaded"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return {"status": "File uploaded", "rfp_id": record.id, "filename": file.filename, "text_length": len(text_content)}

@router.get("/list", response_model=List[RFPResponse])
def list_rfps(db: Session = Depends(get_db)):
    """Get all RFPs"""
    rfps = db.query(RFP).all()
    return rfps

@router.get("/{rfp_id}", response_model=RFPResponse)
def get_rfp(rfp_id: int, db: Session = Depends(get_db)):
    """Get a specific RFP by ID"""
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    return rfp

@router.get("/{rfp_id}/progress")
def get_rfp_progress(rfp_id: int, db: Session = Depends(get_db)):
    """Get current progress of RFP processing"""
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    return {
        "rfp_id": rfp_id,
        "status": rfp.status,
        "current_progress": rfp.current_progress
    }

@router.post("/analyze")
def analyze_rfp_content(rfp: RFPCreate, db: Session = Depends(get_db)):
    """
    Analyze RFP content through Sales and Technical agents
    Returns: JSON with sales summary and technical matches
    """
    # Create RFP record
    record = RFP(title=rfp.title, content=rfp.content, status="analyzing")
    db.add(record)
    db.commit()
    db.refresh(record)
    
    orchestrator = AgentOrchestrator(db)
    
    # Run Sales Agent
    sales_result = orchestrator.run_specific_agent("sales_agent", rfp.content, rfp_id=record.id)
    record.sales_summary = sales_result
    
    # Run Technical Agent
    tech_result = orchestrator.run_specific_agent("technical_agent", rfp.content, rfp_id=record.id, context=sales_result)
    record.technical_matches = tech_result
    
    record.status = "analyzed"
    db.commit()
    
    return {
        "rfp_id": record.id,
        "sales_summary": sales_result,
        "technical_matches": tech_result
    }

@router.post("/{rfp_id}/analyze")
def analyze_rfp(rfp_id: int, db: Session = Depends(get_db)):
    """Process RFP through the complete agent workflow"""
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    orchestrator = AgentOrchestrator(db)
    results = orchestrator.process_rfp_workflow(rfp_id)
    
    # Prepare response with RFP summary and PDF information
    response = {
        "status": "RFP processed successfully",
        "rfp_id": rfp_id,
        "rfp_summary": results.get("rfp_summary"),
        "results": results
    }
    
    # Include PDF information if available
    if "pdf_generated" in results:
        response["response_pdf"] = results["pdf_generated"]
        response["message"] = "Response proposal PDF generated and ready to send to client"
    
    return response

@router.post("/generate_proposal")
def generate_proposal(rfp_id: int, db: Session = Depends(get_db)):
    """
    Generate final proposal from analyzed RFP
    Returns: HTML/PDF proposal document
    """
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    if not rfp.sales_summary or not rfp.technical_matches:
        raise HTTPException(status_code=400, detail="RFP must be analyzed first. Call /analyze endpoint.")
    
    orchestrator = AgentOrchestrator(db)
    
    # Run Pricing Agent
    pricing_result = orchestrator.run_specific_agent(
        "pricing_agent", 
        f"Generate pricing for: {rfp.technical_matches}",
        rfp_id=rfp.id,
        context={"technical_matches": rfp.technical_matches}
    )
    rfp.pricing_data = pricing_result
    
    # Run Proposal Assembly Agent
    proposal_context = {
        "sales_summary": rfp.sales_summary,
        "technical_matches": rfp.technical_matches,
        "pricing_data": pricing_result
    }
    
    final_proposal = orchestrator.run_specific_agent(
        "proposal_assembly_agent",
        f"Create proposal for RFP: {rfp.title}",
        rfp_id=rfp.id,
        context=proposal_context
    )
    
    rfp.final_proposal = final_proposal.get("proposal", "")
    rfp.status = "completed"
    db.commit()
    
    return {
        "rfp_id": rfp.id,
        "status": "Proposal generated successfully",
        "proposal": rfp.final_proposal,
        "format": "HTML"
    }

@router.get("/{rfp_id}/status")
def get_rfp_status(rfp_id: int, db: Session = Depends(get_db)):
    """Get processing status of an RFP"""
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    executions = db.query(AgentExecution).filter(AgentExecution.rfp_id == rfp_id).all()
    
    return {
        "rfp_id": rfp_id,
        "status": rfp.status,
        "executions": [
            {
                "agent_id": e.agent_id,
                "status": e.status,
                "created_at": e.created_at,
                "completed_at": e.completed_at
            }
            for e in executions
        ]
    }

@router.get("/{rfp_id}/proposal-draft")
def get_proposal_draft(rfp_id: int, db: Session = Depends(get_db)):
    """Get the editable proposal draft for human review"""
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    if not rfp.proposal_draft:
        raise HTTPException(status_code=404, detail="Proposal draft not yet generated. Call /rfp/{rfp_id}/analyze first.")
    
    return {
        "rfp_id": rfp_id,
        "title": rfp.title,
        "proposal_draft": rfp.proposal_draft,
        "approval_status": rfp.approval_status,
        "status": rfp.status,
        "instructions": "Edit the sections as needed, then POST to /rfp/{rfp_id}/approve-proposal with the edited content"
    }

@router.post("/{rfp_id}/approve-proposal")
def approve_proposal(rfp_id: int, edited_proposal: dict = Body(...), db: Session = Depends(get_db)):
    """
    Approve and generate PDF from edited proposal draft.
    
    Request body format:
    {
        "title": "Response Proposal for RFP Title",
        "sections": {
            "Executive Summary": "Edited content...",
            "Understanding of Requirements": "Edited content...",
            "Proposed Solution": "Edited content...",
            "Pricing Details": "Edited content...",
            "Payment Terms": "Edited content...",
            "Implementation Timeline": "Edited content...",
            "Terms and Conditions": "Edited content..."
        },
        "approved": true
    }
    """
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    if not rfp.proposal_draft:
        raise HTTPException(status_code=400, detail="No proposal draft available. Generate proposal first.")
    
    if not edited_proposal.get("approved"):
        rfp.approval_status = "rejected"
        rfp.status = "revision_needed"
        db.commit()
        return {
            "status": "Proposal rejected",
            "message": "Proposal needs revision. Regenerate using /rfp/{rfp_id}/analyze"
        }
    
    # Store edited proposal and generate PDF
    rfp.proposal_draft = edited_proposal
    rfp.approval_status = "approved"
    rfp.status = "generating_pdf"
    db.commit()
    
    # Generate PDF using the approved content
    import requests
    import json
    
    try:
        # Prepare PDF generation request
        pdf_payload = {
            "title": edited_proposal.get("title", f"Response Proposal for {rfp.title}"),
            "sections": edited_proposal.get("sections", {}),
            "filename": f"proposal_rfp_{rfp.title.replace(' ', '_')}.pdf"
        }
        
        # Call Flask tool API to generate PDF
        flask_url = "http://localhost:8080/api/generate-proposal-pdf"
        response = requests.post(flask_url, json=pdf_payload, timeout=30)
        
        if response.status_code == 200:
            pdf_result = response.json()
            if pdf_result.get("success"):
                rfp.final_proposal = json.dumps(edited_proposal)
                rfp.status = "completed"
                db.commit()
                
                return {
                    "status": "Proposal approved and PDF generated",
                    "rfp_id": rfp_id,
                    "pdf_info": {
                        "filename": pdf_result.get("filename"),
                        "file_path": pdf_result.get("file_path"),
                        "download_url": pdf_result.get("download_url"),
                        "file_size": pdf_result.get("file_size")
                    },
                    "message": "Response PDF ready to send to client"
                }
        
        raise Exception(f"PDF generation failed: {response.text}")
        
    except Exception as e:
        rfp.status = "pdf_generation_failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

@router.get("/{rfp_id}/proposal")
def get_proposal(rfp_id: int, db: Session = Depends(get_db)):
    """Get the final generated proposal"""
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    if not rfp.final_proposal:
        raise HTTPException(status_code=404, detail="Proposal not yet generated")
    
    return {
        "rfp_id": rfp_id,
        "title": rfp.title,
        "proposal": rfp.final_proposal,
        "sales_summary": rfp.sales_summary,
        "technical_matches": rfp.technical_matches,
        "pricing_data": rfp.pricing_data
    }

@router.delete("/{rfp_id}")
def delete_rfp(rfp_id: int, db: Session = Depends(get_db)):
    """Delete an RFP"""
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    # Delete related records first to avoid foreign key constraint violations
    from models import AgentExecution
    
    # Delete agent executions
    db.query(AgentExecution).filter(AgentExecution.rfp_id == rfp_id).delete()
    
    # Delete associated file if exists
    if rfp.file_path and os.path.exists(rfp.file_path):
        os.remove(rfp.file_path)
    
    # Now delete the RFP
    db.delete(rfp)
    db.commit()
    return {"status": "RFP deleted successfully", "message": f"Deleted RFP {rfp_id} and all related records"}
