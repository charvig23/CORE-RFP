from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from database import SessionLocal
from models import RFP, Agent
from schemas import StepExecutionRequest, StepExecutionResponse
from services.orchestrator import AgentOrchestrator
from typing import Dict, Any

router = APIRouter(prefix="/workflow", tags=["Workflow"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _parse_proposal_to_sections(proposal_text: str) -> Dict[str, str]:
    """Parse proposal text into sections based on common headings"""
    sections = {}
    
    # Common section headers to look for
    section_headers = [
        "Executive Summary",
        "Understanding of Requirements",
        "Requirements Analysis",
        "Proposed Solution",
        "Technical Specifications",
        "Technical Solution",
        "Pricing and Payment Terms",
        "Pricing Breakdown",
        "Payment Terms",
        "Implementation Timeline",
        "Timeline",
        "Terms and Conditions",
        "Terms & Conditions"
    ]
    
    # Try to split by markdown headers (## or #)
    lines = proposal_text.split('\n')
    current_section = "Introduction"
    current_content = []
    
    for line in lines:
        # Check if line is a header
        is_header = False
        header_text = None
        
        # Check for markdown headers
        if line.strip().startswith('##'):
            header_text = line.strip().lstrip('#').strip()
            is_header = True
        elif line.strip().startswith('#'):
            header_text = line.strip().lstrip('#').strip()
            is_header = True
        else:
            # Check if line matches any section header (case insensitive)
            for header in section_headers:
                if header.lower() in line.lower() and len(line.strip()) < 50:
                    header_text = header
                    is_header = True
                    break
        
        if is_header and header_text:
            # Save previous section
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            # Start new section
            current_section = header_text
            current_content = []
        else:
            if line.strip():  # Skip empty lines at section start
                current_content.append(line)
    
    # Save last section
    if current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    # If no sections were found, create a single section
    if not sections:
        sections["Proposal"] = proposal_text
    
    return sections

# Agent execution order
AGENT_PIPELINE = [
    {"name": "sales_agent", "display": "Sales Agent", "description": "Extract requirements and objectives"},
    {"name": "technical_agent", "display": "Technical Agent", "description": "Match SKUs and products"},
    {"name": "pricing_agent", "display": "Pricing Agent", "description": "Generate pricing table"},
    {"name": "proposal_assembly_agent", "display": "Proposal Assembly Agent", "description": "Create final proposal"}
]

@router.post("/execute-step", response_model=StepExecutionResponse)
def execute_workflow_step(request: StepExecutionRequest, db: Session = Depends(get_db)):
    """
    Execute a single step in the agent workflow with HITL approval.
    
    Args:
        rfp_id: The RFP to process
        step_index: Which agent to execute (0=Sales, 1=Technical, 2=Pricing, 3=Proposal)
        context: Previous agent outputs
    
    Returns:
        Agent output and status
    """
    try:
        print(f"\n[WORKFLOW] Executing step {request.step_index} for RFP {request.rfp_id}")
        
        rfp = db.query(RFP).filter(RFP.id == request.rfp_id).first()
        if not rfp:
            raise HTTPException(status_code=404, detail="RFP not found")
        
        if request.step_index < 0 or request.step_index >= len(AGENT_PIPELINE):
            raise HTTPException(status_code=400, detail="Invalid step index")
        
        agent_config = AGENT_PIPELINE[request.step_index]
        print(f"[WORKFLOW] Agent to execute: {agent_config['name']}")
        
        orchestrator = AgentOrchestrator(db)
        
        # Prepare message based on agent type
        if request.step_index == 0:  # Sales Agent
            message = f"Analyze this RFP and extract key requirements, objectives, and scope:\n\n{rfp.content}"
            context = None
            print(f"[WORKFLOW] Sales Agent - analyzing RFP content ({len(rfp.content)} chars)")
        
        elif request.step_index == 1:  # Technical Agent
            if not request.context or 'sales_output' not in request.context:
                raise HTTPException(status_code=400, detail="Sales agent must be executed first. Provide sales_output in context.")
            
            # Extract sales information from the sales_output
            sales_data = request.context.get('sales_output', {})
            sales_response = sales_data.get('agent_response', '')
            
            message = f"Based on the sales analysis, match appropriate SKUs and products. Extract product names and quantities, then use the match_sku_from_csv tool:\n\nRFP Content:\n{rfp.content}\n\nSales Analysis:\n{sales_response}"
            context = request.context
            print(f"[WORKFLOW] Technical Agent - matching SKUs with sales context")
        
        elif request.step_index == 2:  # Pricing Agent
            if not request.context or 'technical_output' not in request.context:
                raise HTTPException(status_code=400, detail="Technical agent must be executed first. Provide technical_output in context.")
            
            technical_data = request.context.get('technical_output', {})
            technical_response = technical_data.get('agent_response', '')
            
            message = f"Generate detailed pricing for the matched products:\n\nTechnical Analysis:\n{technical_response}"
            context = request.context
            print(f"[WORKFLOW] Pricing Agent - generating pricing")
        
        elif request.step_index == 3:  # Proposal Assembly Agent
            if not request.context or 'pricing_output' not in request.context:
                raise HTTPException(status_code=400, detail="Pricing agent must be executed first. Provide pricing_output in context.")
            
            message = f"""Create a comprehensive proposal draft for: {rfp.title}

IMPORTANT: Generate ONLY the proposal text content with these sections:
1. Executive Summary
2. Requirements Analysis
3. Proposed Solution
4. Pricing Breakdown
5. Payment Terms
6. Timeline
7. Terms & Conditions

DO NOT call generate_pdf_proposal or any PDF generation tool.
This is a DRAFT for human review before PDF generation.

Include all context from previous agents."""
            context = request.context
            print(f"[WORKFLOW] Proposal Assembly Agent - creating DRAFT proposal (no PDF)")
        
        # Execute the agent
        print(f"[WORKFLOW] Calling orchestrator.run_specific_agent")
        result = orchestrator.run_specific_agent(
            agent_config["name"],
            message,
            rfp_id=request.rfp_id,
            context=context
        )
        
        print(f"[WORKFLOW] Agent execution completed")
        print(f"[WORKFLOW] Result keys: {result.keys()}")
        
        # Use intelligent routing to determine next step
        routing_decision = orchestrator.select_next_agent(
            current_agent=agent_config["name"],
            current_output=result,
            context=request.context
        )
        
        print(f"[WORKFLOW] Routing decision: {routing_decision}")
        
        # Determine next step based on routing decision
        next_agent_dict = None
        has_next_step = False
        if routing_decision.get("next_agent"):
            # Find the agent in pipeline
            for idx, agent in enumerate(AGENT_PIPELINE):
                if agent["name"] == routing_decision["next_agent"]:
                    next_agent_dict = {
                        "name": agent["display"],
                        "role": agent["name"]
                    }
                    has_next_step = True
                    break
        
        # Check for errors in result
        if result.get("error"):
            raise HTTPException(
                status_code=500, 
                detail=result.get("content", result.get("error_details", "Agent execution failed"))
            )
        
        # Build output dictionary from result
        output_dict = {
            "agent_response": result.get("response", result.get("content", "")),
            "tool_calls": result.get("tool_calls", []),
            "routing": routing_decision
        }
        
        # Build updated context for next agent
        updated_context = request.context.copy() if request.context else {}
        
        # Add current agent's output to context with the correct key
        if request.step_index == 0:  # Sales Agent
            updated_context["sales_output"] = output_dict
        elif request.step_index == 1:  # Technical Agent
            updated_context["technical_output"] = output_dict
        elif request.step_index == 2:  # Pricing Agent
            updated_context["pricing_output"] = output_dict
        elif request.step_index == 3:  # Proposal Assembly Agent
            updated_context["proposal_output"] = output_dict
            # Mark RFP as awaiting approval after proposal draft is generated
            rfp.status = "awaiting_approval"
            rfp.proposal_draft = output_dict
            db.commit()
        
        return StepExecutionResponse(
            rfp_id=request.rfp_id,
            step_index=request.step_index,
            agent_name=agent_config["display"],
            status="completed",
            output=output_dict,
            has_next_step=has_next_step,
            next_agent=next_agent_dict,
            current_context=updated_context
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKFLOW ERROR] Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error executing agent: {str(e)}")

@router.get("/pipeline")
def get_pipeline():
    """Get the complete agent pipeline configuration"""
    return {
        "total_steps": len(AGENT_PIPELINE),
        "pipeline": AGENT_PIPELINE
    }

@router.get("/{rfp_id}/current-state")
def get_workflow_state(rfp_id: int, db: Session = Depends(get_db)):
    """Get current workflow state for an RFP"""
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    # Determine current step
    current_step = 0
    if rfp.sales_summary:
        current_step = 1
    if rfp.technical_matches:
        current_step = 2
    if rfp.pricing_data:
        current_step = 3
    if rfp.final_proposal:
        current_step = 4  # Completed
    
    return {
        "rfp_id": rfp_id,
        "current_step": current_step,
        "completed_steps": current_step,
        "total_steps": len(AGENT_PIPELINE),
        "status": rfp.status,
        "outputs": {
            "sales_summary": rfp.sales_summary,
            "technical_matches": rfp.technical_matches,
            "pricing_data": rfp.pricing_data,
            "final_proposal": rfp.final_proposal
        }
    }

@router.get("/{rfp_id}/proposal-draft")
def get_proposal_draft(rfp_id: int, db: Session = Depends(get_db)):
    """Get the proposal draft for human review"""
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    if not rfp.proposal_draft:
        raise HTTPException(status_code=404, detail="No proposal draft found. Execute proposal agent first.")
    
    return {
        "rfp_id": rfp_id,
        "rfp_title": rfp.title,
        "proposal_draft": rfp.proposal_draft,
        "status": rfp.status
    }

@router.post("/{rfp_id}/approve-proposal")
def approve_proposal(rfp_id: int, request: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """
    Approve proposal and generate PDF (with optional edits)
    
    Body:
    {
        "approved": true/false,
        "edited_proposal": "optional edited proposal text",
        "sections": {} // optional structured edits
    }
    """
    import requests
    
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    if not rfp.proposal_draft:
        raise HTTPException(status_code=400, detail="No proposal draft to approve. Execute proposal agent first.")
    
    approved = request.get("approved", True)
    
    if not approved:
        # User rejected, keep in awaiting_approval state
        rfp.status = "awaiting_approval"
        db.commit()
        return {
            "message": "Proposal rejected. Make edits and resubmit.",
            "status": "awaiting_approval"
        }
    
    # Get edited proposal or use original
    final_proposal_text = request.get("edited_proposal") or rfp.proposal_draft.get("agent_response", "")
    
    print(f"[APPROVAL] Generating PDF for RFP {rfp_id}")
    print(f"[APPROVAL] Proposal text length: {len(final_proposal_text)}")
    print(f"[APPROVAL] RFP title: {rfp.title}")
    
    # Parse proposal text into sections for PDF generation
    sections = _parse_proposal_to_sections(final_proposal_text)
    print(f"[APPROVAL] Parsed {len(sections)} sections")
    
    # Call Flask API to generate PDF
    try:
        flask_url = "http://localhost:8080/api/generate-proposal-pdf"
        print(f"[APPROVAL] Calling Flask API: {flask_url}")
        
        flask_response = requests.post(
            flask_url,
            json={
                "title": rfp.title,
                "sections": sections,
                "filename": f"proposal_rfp_{rfp_id}.pdf"
            },
            timeout=30
        )
        
        print(f"[APPROVAL] Flask response status: {flask_response.status_code}")
        
        if flask_response.status_code == 200:
            pdf_data = flask_response.json()
            print(f"[APPROVAL] PDF generated: {pdf_data}")
            
            # Update RFP with final proposal and PDF info
            rfp.final_proposal = final_proposal_text
            rfp.status = "completed"
            rfp.pdf_filename = pdf_data.get("filename")
            rfp.pdf_url = pdf_data.get("download_url")
            db.commit()
            
            return {
                "message": "Proposal approved and PDF generated successfully",
                "status": "completed",
                "proposal_text": final_proposal_text,
                "pdf_filename": pdf_data.get("filename"),
                "pdf_url": pdf_data.get("download_url"),
                "pdf_download_link": pdf_data.get("download_url")
            }
        else:
            error_msg = flask_response.text
            print(f"[APPROVAL ERROR] Flask error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {error_msg}")
            
    except requests.exceptions.RequestException as e:
        print(f"[APPROVAL ERROR] Request exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to PDF service: {str(e)}")
    except Exception as e:
        print(f"[APPROVAL ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error during approval: {str(e)}")
