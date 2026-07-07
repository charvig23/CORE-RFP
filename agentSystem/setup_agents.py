from database import SessionLocal
from models import Agent, Tool
import uuid

def generate_uuid():
    return str(uuid.uuid4())

def seed_agents():
    db = SessionLocal()
    
    try:
        # Check if agents already exist
        existing = db.query(Agent).count()
        if existing > 0:
            print(f"✓ Agents already seeded ({existing} found), skipping")
            return

        agents = [
            Agent(
                id=generate_uuid(),
                name="Sales Agent",
                role="sales",
                system_prompt="""You are a Sales Analysis Agent specialized in analyzing RFP documents.
Your job is to extract and structure the following information from the RFP:
- Business objectives and goals
- Project scope and requirements
- Timeline and deadlines
- Budget constraints if mentioned
- Key stakeholders
- Evaluation criteria

Return your analysis as a structured JSON with these exact keys:
{
    "objectives": [],
    "scope": "",
    "requirements": [],
    "timeline": "",
    "budget": "",
    "stakeholders": [],
    "evaluation_criteria": []
}""",
                model="gemini-2.0-flash",
                tool_ids=[]
            ),
            Agent(
                id=generate_uuid(),
                name="Technical Agent",
                role="technical",
                system_prompt="""You are a Technical Analysis Agent specialized in matching RFP requirements to products.
You will receive the sales analysis of an RFP.
Your job is to identify technical requirements and match them to appropriate SKUs/products.
Use the match_skus tool to find matching products for each requirement.

Return your analysis as structured JSON with these exact keys:
{
    "technical_requirements": [],
    "matched_products": [],
    "recommended_solutions": [],
    "implementation_notes": ""
}""",
                model="gemini-2.0-flash",
                tool_ids=["match_skus"]
            ),
            Agent(
                id=generate_uuid(),
                name="Pricing Agent",
                role="pricing",
                system_prompt="""You are a Pricing Agent specialized in creating cost breakdowns for proposals.
You will receive the technical analysis with matched products/SKUs.
Your job is to create a detailed pricing breakdown.

Return your analysis as structured JSON with these exact keys:
{
    "line_items": [],
    "subtotal": 0,
    "tax": 0,
    "total": 0,
    "pricing_notes": "",
    "validity_period": "30 days"
}""",
                model="gemini-2.0-flash",
                tool_ids=["get_pricing"]
            ),
            Agent(
                id=generate_uuid(),
                name="Proposal Assembly Agent",
                role="proposal",
                system_prompt="""You are a Proposal Assembly Agent specialized in writing professional business proposals.
You will receive the sales analysis, technical matches, and pricing data.
Your job is to assemble a complete, professional proposal.

Return your proposal as structured JSON with these exact keys:
{
    "executive_summary": "",
    "company_introduction": "",
    "understanding_of_requirements": "",
    "proposed_solution": "",
    "technical_approach": "",
    "pricing_summary": "",
    "timeline": "",
    "terms_and_conditions": "",
    "conclusion": ""
}""",
                model="gemini-2.0-flash",
                tool_ids=[]
            )
        ]

        for agent in agents:
            db.add(agent)
        
        db.commit()
        print(f"✓ Successfully seeded {len(agents)} agents")
        
        # Verify
        for agent in agents:
            print(f"  - {agent.name} ({agent.role})")

    except Exception as e:
        print(f"✗ Error seeding agents: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_agents()