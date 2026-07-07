from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Agent, Tool
from schemas import AgentResponse, ToolResponse

router = APIRouter()

@router.get("/agents/list")
def list_agents(db: Session = Depends(get_db)):
    agents = db.query(Agent).all()
    return {"agents": agents, "total": len(agents)}

@router.get("/agents/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        return {"error": "Agent not found"}
    return agent

@router.get("/tools/list")
def list_tools(db: Session = Depends(get_db)):
    tools = db.query(Tool).all()
    return {"tools": tools, "total": len(tools)}