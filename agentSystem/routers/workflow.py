from sqlalchemy.orm import Session
from database import get_db
from models import RFP, AgentExecution
from schemas import RFPResponse, ApproveProposalRequest, RFPStatusResponse
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Form
import uuid
import os
import PyPDF2
import io

router = APIRouter()

def generate_uuid():
    return str(uuid.uuid4())

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"Could not extract PDF text: {e}"

@router.post("/rfp/upload")
async def upload_rfp(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(None),
    user_id: str = Form(None),
    db: Session = Depends(get_db)
):
    rfp_id = generate_uuid()
    raw_text = ""
    filename = "manual_entry"

    if file:
        filename = file.filename
        file_bytes = await file.read()

        if filename.endswith(".pdf"):
            raw_text = extract_text_from_pdf(file_bytes)
        else:
            raw_text = file_bytes.decode("utf-8", errors="ignore")

        # Save file to uploads folder
        upload_path = f"uploads/{rfp_id}_{filename}"
        with open(upload_path, "wb") as f:
            f.write(file_bytes)

    # Create RFP record in DB
    rfp = RFP(
        id=rfp_id,
        filename=filename,
        user_id=user_id,
        raw_text=raw_text,
        status="uploaded",
        approval_status="pending",
        current_progress={
            "sales": "pending",
            "technical": "pending",
            "pricing": "pending",
            "proposal": "pending"
        }
    )
    db.add(rfp)
    db.commit()
    db.refresh(rfp)

    # Trigger pipeline in background
    background_tasks.add_task(run_pipeline, rfp_id)

    return {
        "message": "RFP uploaded successfully, pipeline started",
        "rfp_id": rfp_id,
        "filename": filename,
        "text_length": len(raw_text)
    }

@router.get("/rfp/{rfp_id}/status")
def get_rfp_status(rfp_id: str, db: Session = Depends(get_db)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    return {
        "id": rfp.id,
        "status": rfp.status,
        "approval_status": rfp.approval_status,
        "current_progress": rfp.current_progress
    }

@router.get("/rfp/{rfp_id}")
def get_rfp(rfp_id: str, db: Session = Depends(get_db)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    return rfp

@router.get("/rfp/list/all")
def list_rfps(db: Session = Depends(get_db)):
    rfps = db.query(RFP).all()
    return {"rfps": rfps, "total": len(rfps)}

@router.post("/rfp/{rfp_id}/approve-proposal")
def approve_proposal(
    rfp_id: str,
    request: ApproveProposalRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")

    if request.edited_proposal:
        rfp.proposal_draft = request.edited_proposal

    rfp.approval_status = "approved"
    rfp.status = "approved"
    db.commit()

    return {"message": "Proposal approved", "rfp_id": rfp_id}

def run_pipeline(rfp_id: str):
    from services.orchestrator import orchestrator
    orchestrator.run_pipeline(rfp_id)