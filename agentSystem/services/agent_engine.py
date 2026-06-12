import os
import google.generativeai as genai
from models import Conversation, Agent, Tool
from services.tool_runtime import tool_runtime
from sqlalchemy.orm import Session

# Configure Google Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def run_agent(db: Session, agent_name: str, message: str):
    agent: Agent = db.query(Agent).filter(Agent.name == agent_name).first()
    if not agent:
        return "Agent not found."

    # Create model instance using the agent's configured model
    agent_model = genai.GenerativeModel(
        agent.model,
        generation_config={"temperature": 0.7}
    )

    tool_objs = db.query(Tool).filter(Tool.name.in_(agent.tools)).all()
    tool_runtime.load_from_db(tool_objs)

    # load conversation memory
    history = db.query(Conversation).filter(Conversation.agent_name == agent_name).all()
    history_messages = "\\n".join([f"User: {h.message}\\nAssistant: {h.response or ''}" for h in history])

    prompt = f"{agent.system_prompt}\\n\\nConversation History:\\n{history_messages}\\n\\nUser: {message}\\n\\nAssistant:"

    response = agent_model.generate_content(prompt)

    reply = response.text.strip()

    # store in DB
    convo = Conversation(agent_name=agent_name, message=message, response=reply)
    db.add(convo)
    db.commit()

    return reply
