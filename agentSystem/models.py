from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, CHAR
from database import Base
from datetime import datetime
import uuid

class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type.

    Uses PostgreSQL's UUID type, otherwise stores as CHAR(36) string.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID as PGUUID
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        # other dialects store as string
        return str(value) if isinstance(value, uuid.UUID) else str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))

class Tool(Base):
    __tablename__ = "tools"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    code = Column(Text)  # Python function code or API endpoint URL
    tool_type = Column(String, default="function")  # "function" or "api"
    parameters = Column(JSON)  # JSON schema for parameters
    created_at = Column(DateTime, default=datetime.utcnow)

class Agent(Base):
    __tablename__ = "agents"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, index=True)
    role = Column(String)  # "sales", "technical", "pricing", "proposal_assembly"
    system_prompt = Column(Text)  # System prompt defining agent behavior
    model = Column(String, default="gemini-2.5-flash")
    tool_ids = Column(JSON)  # List of tool IDs assigned to this agent
    created_at = Column(DateTime, default=datetime.utcnow)

class RFP(Base):
    __tablename__ = "rfps"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text)
    file_path = Column(String, nullable=True)
    status = Column(String, default="uploaded")  # uploaded, analyzed, processed, awaiting_approval, approved
    current_progress = Column(JSON, nullable=True)  # Real-time progress: {agent: "sales_agent", tool: "extract_sales_objectives", status: "running"}
    sales_summary = Column(JSON, nullable=True)  # Output from Sales Agent
    technical_matches = Column(JSON, nullable=True)  # Output from Technical Agent
    pricing_data = Column(JSON, nullable=True)  # Output from Pricing Agent
    proposal_draft = Column(JSON, nullable=True)  # Draft proposal for human review (editable)
    approval_status = Column(String, default="pending")  # pending, approved, rejected
    final_proposal = Column(Text, nullable=True)  # Output from Proposal Agent (after approval)
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(GUID(), ForeignKey("agents.id"))
    rfp_id = Column(Integer, ForeignKey("rfps.id"), nullable=True)
    message = Column(Text)
    response = Column(Text)
    tool_calls = Column(JSON, nullable=True)  # Track which tools were called
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentExecution(Base):
    __tablename__ = "agent_executions"
    id = Column(Integer, primary_key=True, index=True)
    rfp_id = Column(Integer, ForeignKey("rfps.id"))
    agent_id = Column(GUID(), ForeignKey("agents.id"))
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(String)  # "pending", "running", "completed", "failed"
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
