from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Agent, Tool
from schemas import (
    AgentCreate, AgentUpdate, AgentResponse, 
    AgentMessageRequest, MessageRequest
)
from services.orchestrator import AgentOrchestrator
from typing import List
from uuid import UUID

router = APIRouter(prefix="/agents", tags=["Agents"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create", response_model=AgentResponse)
def create_agent(data: AgentCreate, db: Session = Depends(get_db)):
    """Create a new agent with role, system prompt, and assigned tools"""
    # Check if agent name already exists
    existing = db.query(Agent).filter(Agent.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Agent with this name already exists")
    
    # Verify all tool IDs exist
    if data.tool_ids:
        tools = db.query(Tool).filter(Tool.id.in_(data.tool_ids)).all()
        if len(tools) != len(data.tool_ids):
            raise HTTPException(status_code=400, detail="One or more tool IDs not found")
    
    agent = Agent(
        name=data.name,
        role=data.role,
        system_prompt=data.system_prompt,
        model=data.model,
        tool_ids=data.tool_ids
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

@router.get("/list", response_model=List[AgentResponse])
def list_agents(db: Session = Depends(get_db)):
    """Get all agents"""
    agents = db.query(Agent).all()
    return agents

@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: UUID, db: Session = Depends(get_db)):
    """Get a specific agent by ID"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: UUID, data: AgentUpdate, db: Session = Depends(get_db)):
    """Update an agent's configuration"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if data.system_prompt is not None:
        agent.system_prompt = data.system_prompt
    if data.model is not None:
        agent.model = data.model
    if data.tool_ids is not None:
        # Verify all tool IDs exist
        tools = db.query(Tool).filter(Tool.id.in_(data.tool_ids)).all()
        if len(tools) != len(data.tool_ids):
            raise HTTPException(status_code=400, detail="One or more tool IDs not found")
        agent.tool_ids = data.tool_ids
    
    db.commit()
    db.refresh(agent)
    return agent

@router.delete("/{agent_id}")
def delete_agent(agent_id: UUID, db: Session = Depends(get_db)):
    """Delete an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    return {"status": "Agent deleted successfully"}

@router.post("/{agent_id}/add-tools")
def add_tools_to_agent(agent_id: UUID, tool_ids: List[UUID] = Body(...), db: Session = Depends(get_db)):
    """Add tools to an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Verify all tool IDs exist
    tools = db.query(Tool).filter(Tool.id.in_(tool_ids)).all()
    if len(tools) != len(tool_ids):
        raise HTTPException(status_code=400, detail="One or more tool IDs not found")
    
    # Convert UUID objects to strings for JSON storage
    tool_id_strings = [str(tid) for tid in tool_ids]
    
    # Add new tools to existing ones
    current_tools = set(agent.tool_ids or [])
    current_tools.update(tool_id_strings)
    agent.tool_ids = list(current_tools)
    
    db.commit()
    return {"status": "Tools added successfully", "tool_ids": agent.tool_ids}

@router.post("/{agent_id}/remove-tools")
def remove_tools_from_agent(agent_id: UUID, tool_ids: List[UUID], db: Session = Depends(get_db)):
    """Remove tools from an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Convert UUID objects to strings for comparison
    tool_id_strings = [str(tid) for tid in tool_ids]
    
    # Remove tools from current list
    current_tools = set(agent.tool_ids or [])
    current_tools.difference_update(tool_id_strings)
    agent.tool_ids = list(current_tools)
    
    db.commit()
    return {"status": "Tools removed successfully", "tool_ids": agent.tool_ids}
    
    # Remove tools
    current_tools = set(agent.tool_ids or [])
    current_tools.difference_update(tool_ids)
    agent.tool_ids = list(current_tools)
    
    db.commit()
    return {"status": "Tools removed successfully", "tool_ids": agent.tool_ids}

@router.post("/{agent_id}/execute")
def execute_agent(agent_id: UUID, request: AgentMessageRequest, db: Session = Depends(get_db)):
    """Execute a specific agent with a message"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if request.agent_id is not None and request.agent_id != agent_id:
        raise HTTPException(status_code=400, detail="Request agent_id does not match the path parameter")
    
    orchestrator = AgentOrchestrator(db)
    result = orchestrator.execute_agent(agent, request.message, request.context)
    return result

@router.post("/orchestrate")
def orchestrate_message(request: MessageRequest, db: Session = Depends(get_db)):
    """Automatically select and execute the best agent for the message"""
    agents = db.query(Agent).all()
    if not agents:
        raise HTTPException(status_code=404, detail="No agents available")
    
    orchestrator = AgentOrchestrator(db)
    selected_agent = orchestrator.select_agent(request.message, agents)
    result = orchestrator.execute_agent(selected_agent, request.message)
    
    return {
        "selected_agent": selected_agent.name,
        "result": result
    }
