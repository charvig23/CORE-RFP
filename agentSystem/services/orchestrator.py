import os
import json
import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import RFP, Agent, AgentExecution, Conversation
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

FLASK_BASE_URL = "http://127.0.0.1:8080"

class AgentOrchestrator:

    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def update_progress(self, db: Session, rfp_id: str, agent_role: str, status: str):
        rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
        if rfp:
            progress = rfp.current_progress or {}
            progress[agent_role] = status
            rfp.current_progress = progress
            db.commit()
            print(f"  Progress updated: {agent_role} → {status}")

    def call_gemini(self, system_prompt: str, user_message: str) -> str:
        try:
            full_prompt = f"{system_prompt}\n\n{user_message}"
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"  Gemini error: {e}")
            return "{}"

    def parse_json_response(self, text: str) -> dict:
        try:
            # Remove markdown code blocks if present
            text = text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except Exception:
            return {"raw_response": text}

    def call_flask_tool(self, endpoint: str, payload: dict) -> dict:
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{FLASK_BASE_URL}{endpoint}",
                    json=payload
                )
                return response.json()
        except Exception as e:
            print(f"  Flask tool error: {e}")
            return {"error": str(e)}

    def run_sales_agent(self, db: Session, rfp: RFP, agent: Agent) -> dict:
        print(f"\n→ Running Sales Agent")
        self.update_progress(db, rfp.id, "sales", "running")

        user_message = f"""Please analyze this RFP document and extract the required information:

RFP CONTENT:
{rfp.raw_text[:4000]}

Return ONLY a JSON object with no extra text."""

        raw_response = self.call_gemini(agent.system_prompt, user_message)
        result = self.parse_json_response(raw_response)

        rfp.sales_summary = result
        self.update_progress(db, rfp.id, "sales", "completed")
        db.commit()

        print(f"  Sales Agent completed")
        return result

    def run_technical_agent(self, db: Session, rfp: RFP, agent: Agent) -> dict:
        print(f"\n→ Running Technical Agent")
        self.update_progress(db, rfp.id, "technical", "running")

        user_message = f"""Based on this sales analysis, identify technical requirements and match products:

SALES ANALYSIS:
{json.dumps(rfp.sales_summary, indent=2)}

Return ONLY a JSON object with no extra text."""

        raw_response = self.call_gemini(agent.system_prompt, user_message)
        result = self.parse_json_response(raw_response)

        rfp.technical_matches = result
        self.update_progress(db, rfp.id, "technical", "completed")
        db.commit()

        print(f"  Technical Agent completed")
        return result

    def run_pricing_agent(self, db: Session, rfp: RFP, agent: Agent) -> dict:
        print(f"\n→ Running Pricing Agent")
        self.update_progress(db, rfp.id, "pricing", "running")

        user_message = f"""Based on these technical matches, create a detailed pricing breakdown:

TECHNICAL MATCHES:
{json.dumps(rfp.technical_matches, indent=2)}

Return ONLY a JSON object with no extra text."""

        raw_response = self.call_gemini(agent.system_prompt, user_message)
        result = self.parse_json_response(raw_response)

        rfp.pricing_data = result
        self.update_progress(db, rfp.id, "pricing", "completed")
        db.commit()

        print(f"  Pricing Agent completed")
        return result

    def run_proposal_agent(self, db: Session, rfp: RFP, agent: Agent) -> dict:
        print(f"\n→ Running Proposal Assembly Agent")
        self.update_progress(db, rfp.id, "proposal", "running")

        user_message = f"""Assemble a complete professional proposal using all this information:

SALES ANALYSIS:
{json.dumps(rfp.sales_summary, indent=2)}

TECHNICAL MATCHES:
{json.dumps(rfp.technical_matches, indent=2)}

PRICING DATA:
{json.dumps(rfp.pricing_data, indent=2)}

Return ONLY a JSON object with no extra text."""

        raw_response = self.call_gemini(agent.system_prompt, user_message)
        result = self.parse_json_response(raw_response)

        rfp.proposal_draft = result
        rfp.status = "awaiting_approval"
        self.update_progress(db, rfp.id, "proposal", "completed")
        db.commit()

        print(f"  Proposal Agent completed")
        return result

    def run_pipeline(self, rfp_id: str):
        db = SessionLocal()
        try:
            rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
            if not rfp:
                print(f"RFP {rfp_id} not found")
                return

            print(f"\n{'='*50}")
            print(f"Starting pipeline for RFP: {rfp.filename}")
            print(f"{'='*50}")

            rfp.status = "processing"
            db.commit()

            # Load agents from DB
            sales_agent = db.query(Agent).filter(Agent.role == "sales").first()
            technical_agent = db.query(Agent).filter(Agent.role == "technical").first()
            pricing_agent = db.query(Agent).filter(Agent.role == "pricing").first()
            proposal_agent = db.query(Agent).filter(Agent.role == "proposal").first()

            if not all([sales_agent, technical_agent, pricing_agent, proposal_agent]):
                print("ERROR: Not all agents found in DB. Run setup_agents.py first.")
                return

            # Run agents in sequence
            self.run_sales_agent(db, rfp, sales_agent)
            self.run_technical_agent(db, rfp, technical_agent)
            self.run_pricing_agent(db, rfp, pricing_agent)
            self.run_proposal_agent(db, rfp, proposal_agent)

            print(f"\n{'='*50}")
            print(f"Pipeline complete! Status: awaiting_approval")
            print(f"{'='*50}\n")

        except Exception as e:
            print(f"Pipeline error: {e}")
            if rfp:
                rfp.status = "error"
                db.commit()
        finally:
            db.close()


orchestrator = AgentOrchestrator()