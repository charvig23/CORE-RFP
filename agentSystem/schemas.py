from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    model: str
    tool_ids: list
    created_at: datetime

    class Config:
        from_attributes = True


class ToolResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    endpoint: Optional[str]
    parameters: dict
    created_at: datetime

    class Config:
        from_attributes = True


class RFPResponse(BaseModel):
    id: str
    filename: Optional[str]
    status: str
    approval_status: str
    sales_summary: Optional[Any]
    technical_matches: Optional[Any]
    pricing_data: Optional[Any]
    proposal_draft: Optional[Any]
    final_proposal: Optional[str]
    current_progress: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ApproveProposalRequest(BaseModel):
    edited_proposal: Optional[Any] = None


class RFPStatusResponse(BaseModel):
    id: str
    status: str
    approval_status: str
    current_progress: Optional[Any]

    class Config:
        from_attributes = True