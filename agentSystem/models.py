import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    system_prompt = Column(Text, nullable=False)
    model = Column(String, default="gemini-2.0-flash")
    tool_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class Tool(Base):
    __tablename__ = "tools"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text)
    endpoint = Column(String)
    parameters = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class RFP(Base):
    __tablename__ = "rfps"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String)
    user_id = Column(String, nullable=True)
    raw_text = Column(Text)
    status = Column(String, default="uploaded")
    approval_status = Column(String, default="pending")
    sales_summary = Column(JSON)
    technical_matches = Column(JSON)
    pricing_data = Column(JSON)
    proposal_draft = Column(JSON)
    final_proposal = Column(Text)
    current_progress = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(String, primary_key=True, default=generate_uuid)
    rfp_id = Column(String, nullable=False)
    agent_id = Column(String, nullable=False)
    agent_name = Column(String)
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(String, default="running")
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    rfp_id = Column(String)
    agent_id = Column(String)
    agent_name = Column(String)
    message = Column(Text)
    response = Column(Text)
    tool_calls = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)