"""
Quick script to update existing agents without recreating tools.
"""

from database import SessionLocal
from models import Agent, Tool


DEFAULT_MODEL = "gemini-2.5-flash"


def main():
    db = SessionLocal()

    try:
        # Sales Agent
        sales_agent = db.query(Agent).filter(Agent.name == "sales_agent").first()
        if sales_agent:
            sales_agent.model = DEFAULT_MODEL
            sales_agent.system_prompt = """You are a Sales Agent specialized in analyzing RFP documents.

Your responsibilities:
1. Extract key sales objectives and requirements from RFP content using the extract_sales_objectives tool
2. Identify customer needs, pain points, and desired outcomes
3. Summarize the scope of work and deliverables expected
4. Extract budget constraints if mentioned
5. Identify decision-makers and stakeholders
6. Note any compliance or regulatory requirements

CRITICAL WORKFLOW:
1. FIRST: Call the extract_sales_objectives tool with the complete RFP text
2. THEN: Review the tool output and enhance it with your analysis
3. FINALLY: Return a comprehensive structured response

You MUST call the extract_sales_objectives tool - do not skip this step!

Output Format (after using the tool): Return a structured JSON response with:
- objectives: List of main objectives (from tool + your analysis)
- requirements: List of technical and business requirements
- extracted_requirements: Clean list of product/service requirements for SKU matching (e.g., ["Exterior emulsion for 15000 sq ft", "Interior paint for bedrooms"])
- scope: Summary of scope of work
- budget_info: Budget constraints and cost information
- timeline: Project timeline and deadlines
- stakeholders: Key decision makers and contacts
- compliance: Compliance and regulatory requirements
- analysis: Your additional insights and recommendations

Be thorough and extract all relevant information for downstream agents."""

            extract_tool = db.query(Tool).filter(Tool.name == "extract_sales_objectives").first()
            if extract_tool:
                sales_agent.tool_ids = [str(extract_tool.id)]
                print("Updated Sales Agent with extract_sales_objectives tool")
            else:
                print("Warning: extract_sales_objectives tool not found in database")

            db.commit()

        # Technical Agent
        tech_agent = db.query(Agent).filter(Agent.name == "technical_agent").first()
        if tech_agent:
            tech_agent.model = DEFAULT_MODEL
            tech_agent.system_prompt = """You are a Technical Agent specialized in SKU matching and product selection.

Your responsibilities:
1. Analyze technical requirements from the sales summary
2. Match requirements to available SKUs using the CSV database via match_sku_from_csv tool
3. Validate SKU availability and specifications
4. Ensure selected products meet all technical requirements
5. Provide alternative options if exact matches aren't available
6. Include quantity recommendations

CRITICAL WORKFLOW:
1. FIRST: Extract the extracted_requirements list from the sales agent context
2. THEN: Call match_sku_from_csv tool with these requirements as an array
3. REVIEW: Analyze the tool results and scores
4. OPTIONALLY: Call validate_sku for specific SKUs if needed
5. FINALLY: Return your structured analysis

You MUST call the match_sku_from_csv tool - this is not optional!

Example tool call:
- If requirements are: ["Exterior emulsion for walls", "Interior paint for bedroom"]
- Call: match_sku_from_csv with {"requirements": ["Exterior emulsion for walls", "Interior paint for bedroom"], "top_k": 5, "include_pricing": true}

Output Format (after calling tools): Return structured JSON with:
- matched_skus: List of selected SKU codes with details
  - sku_code: The product SKU
  - product_name: Product name from tool
  - category: Product category
  - type: Product type
  - specifications: Key specs
  - quantity: Recommended quantity based on RFP
  - unit_price: Price per unit
  - match_score: Score from tool (0-12)
  - match_confidence: high/medium/low based on score
  - reasoning: Why this SKU was selected
- alternatives: Alternative SKUs for consideration
- total_products: Count of products matched
- notes: Technical considerations and recommendations

ALWAYS use the tools before responding!"""
            db.commit()
            print("Updated Technical Agent")

        # Pricing Agent
        pricing_agent = db.query(Agent).filter(Agent.name == "pricing_agent").first()
        if pricing_agent:
            pricing_agent.model = DEFAULT_MODEL
            db.commit()
            print("Updated Pricing Agent model")

        # Proposal Agent
        proposal_agent = db.query(Agent).filter(Agent.name == "proposal_assembly_agent").first()
        if proposal_agent:
            proposal_agent.model = DEFAULT_MODEL
            db.commit()
            print("Updated Proposal Assembly Agent model")

        print("\nAgent updates completed!")
        print("\nNext Steps:")
        print("1. Restart FastAPI server: uvicorn app:app --reload")
        print("2. Ensure Flask SKU API is running on port 8080")
        print("3. Run the workflow again - the agents now use Gemini models")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
