from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Tool
from schemas import ToolCreate, ToolUpdate, ToolResponse, ToolExecutionRequest
from typing import List
from uuid import UUID

router = APIRouter(prefix="/tools", tags=["Tools"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create", response_model=ToolResponse)
def create_tool(data: ToolCreate, db: Session = Depends(get_db)):
    """Create a new tool (function or API endpoint)"""
    # Check if tool name already exists
    existing = db.query(Tool).filter(Tool.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tool with this name already exists")
    
    tool = Tool(
        name=data.name,
        description=data.description,
        code=data.code,
        tool_type=data.tool_type,
        parameters=data.parameters
    )
    db.add(tool)
    db.commit()
    db.refresh(tool)
    return tool

@router.get("/list", response_model=List[ToolResponse])
def list_tools(db: Session = Depends(get_db)):
    """Get all available tools"""
    tools = db.query(Tool).all()
    return tools

@router.get("/{tool_id}", response_model=ToolResponse)
def get_tool(tool_id: UUID, db: Session = Depends(get_db)):
    """Get a specific tool by ID"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool

@router.put("/{tool_id}", response_model=ToolResponse)
def update_tool(tool_id: UUID, data: ToolUpdate, db: Session = Depends(get_db)):
    """Update a tool's configuration"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    if data.description is not None:
        tool.description = data.description
    if data.code is not None:
        tool.code = data.code
    if data.parameters is not None:
        tool.parameters = data.parameters
    
    db.commit()
    db.refresh(tool)
    return tool

@router.delete("/{tool_id}")
def delete_tool(tool_id: UUID, db: Session = Depends(get_db)):
    """Delete a tool"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    db.delete(tool)
    db.commit()
    return {"status": "Tool deleted successfully"}

@router.post("/execute")
def execute_tool(request: ToolExecutionRequest, db: Session = Depends(get_db)):
    """Execute a tool directly with parameters"""
    from services.orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator(db)
    tool = db.query(Tool).filter(Tool.id == request.tool_id).first()
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    result = orchestrator.execute_tool(tool.name, request.parameters)
    return {"tool_name": tool.name, "result": result}
