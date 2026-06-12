from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID

# Tool Schemas
class ToolCreate(BaseModel):
    name: str
    description: str
    code: str
    tool_type: str = "function"  # "function" or "api"
    parameters: Optional[Dict[str, Any]] = None

class ToolUpdate(BaseModel):
    description: Optional[str] = None
    code: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class ToolResponse(BaseModel):
    id: UUID
    name: str
    description: str
    tool_type: str
    parameters: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

# Agent Schemas
class AgentCreate(BaseModel):
    name: str
    role: str  # "sales", "technical", "pricing", "proposal_assembly"
    system_prompt: str
    model: str = "gemini-2.5-flash"
    tool_ids: List[UUID] = []

class AgentUpdate(BaseModel):
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    tool_ids: Optional[List[UUID]] = None

class AgentResponse(BaseModel):
    id: UUID
    name: str
    role: str
    system_prompt: str
    model: str
    tool_ids: List[UUID]
    
    class Config:
        from_attributes = True

# RFP Schemas
class RFPCreate(BaseModel):
    title: str
    content: str

class RFPResponse(BaseModel):
    id: int
    title: str
    status: str
    sales_summary: Optional[Dict[str, Any]]
    technical_matches: Optional[Dict[str, Any]]
    pricing_data: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

# Message/Orchestration Schemas
class MessageRequest(BaseModel):
    message: str
    rfp_id: Optional[int] = None

class AgentMessageRequest(BaseModel):
    agent_id: Optional[UUID] = None
    message: str
    context: Optional[Dict[str, Any]] = None

class OrchestrationRequest(BaseModel):
    rfp_id: int
    
class ToolExecutionRequest(BaseModel):
    tool_id: UUID
    parameters: Dict[str, Any]

# Workflow Schemas
class StepExecutionRequest(BaseModel):
    rfp_id: int
    step_index: int  # 0=Sales, 1=Technical, 2=Pricing, 3=Proposal
    context: Optional[Dict[str, Any]] = None

class StepExecutionResponse(BaseModel):
    rfp_id: int
    step_index: int
    agent_name: str
    status: str
    output: Dict[str, Any]
    has_next_step: bool
    next_agent: Optional[Dict[str, str]] = None
    current_context: Dict[str, Any]
