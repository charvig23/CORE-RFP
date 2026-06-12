"""
Setup script to create all agents and tools for the RFP processing system.
Run this once to populate the database with the required agents and tools.
"""

import sys
from database import SessionLocal, engine, Base
from models import Agent, Tool

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Create all tables
Base.metadata.create_all(bind=engine)

DEFAULT_MODEL = "gemini-2.5-flash"

def setup_tools(db):
    """Create all tools for the agents"""
    
    tools = [
        # Sales Agent Tools
        {
            "name": "extract_sales_objectives",
            "description": "Extract sales objectives, requirements, scope, budget, and key information from RFP text. Returns structured data with all extracted fields.",
            "tool_type": "api",
            "code": "http://localhost:8080/api/extract-sales-objectives",
            "parameters": {
                "type": "object",
                "properties": {
                    "rfp_text": {"type": "string", "description": "The complete RFP content to analyze"}
                },
                "required": ["rfp_text"]
            }
        },
        
        # Technical Agent Tools
        {
            "name": "match_sku_from_csv",
            "description": "Match product SKUs from CSV file based on requirements and return ranked SKU matches with price and metadata.",
            "tool_type": "api",
            "code": "http://localhost:8080/api/match-sku",  # Update to deployed Render URL when ready
            "parameters": {
                "type": "object",
                "properties": {
                    "requirements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of plain-English product requirements to match, e.g. ['Exterior emulsion for outer walls']"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of top matches to return per requirement. Defaults to 3.",
                        "default": 3
                    },
                    "include_pricing": {
                        "type": "boolean",
                        "description": "When true, attach pricing rows (if available).",
                        "default": True
                    }
                },
                "required": ["requirements"]
            }
        },
        {
            "name": "validate_sku",
            "description": "Validate SKU exists and get details",
            "tool_type": "api",
            "code": "http://localhost:8080/api/validate-sku",  # Update to deployed Render URL when ready
            "parameters": {
                "type": "object",
                "properties": {
                    "sku_code": {"type": "string", "description": "The SKU code to validate"}
                },
                "required": ["sku_code"]
            }
        },
        
        # Pricing Agent Tools
        {
            "name": "generate_pricing_table",
            "description": "Generate pricing table for matched SKUs. Calls external API for pricing calculation.",
            "tool_type": "api",
            "code": "http://localhost:8080/api/generate-pricing-table",
            "parameters": {
                "type": "object",
                "properties": {
                    "skus": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "sku_code": {"type": "string"},
                                "quantity": {"type": "integer"}
                            }
                        },
                        "description": "List of SKUs with quantities"
                    },
                    "discount_rate": {
                        "type": "number",
                        "description": "Discount percentage to apply"
                    }
                },
                "required": ["skus"]
            }
        },
        {
            "name": "calculate_total_cost",
            "description": "Calculate total cost with taxes and discounts",
            "tool_type": "api",
            "code": "http://localhost:8080/api/calculate-total-cost",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of items with price and quantity"
                    },
                    "tax_rate": {"type": "number", "description": "Tax rate (default 0.18 for 18%)"},
                    "discount": {"type": "number", "description": "Discount percentage"}
                },
                "required": ["items"]
            }
        },
        
        # Proposal Assembly Agent Tools
        {
            "name": "format_proposal_html",
            "description": "Format proposal content as HTML document",
            "tool_type": "api",
            "code": "http://localhost:8080/api/format-proposal-html",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Proposal title"},
                    "sections": {
                        "type": "object",
                        "description": "Dictionary of section names and content"
                    }
                },
                "required": ["title", "sections"]
            }
        },
        {
            "name": "generate_pdf_proposal",
            "description": "Generate PDF from proposal content. Calls external API.",
            "tool_type": "api",
            "code": "http://localhost:8080/api/generate-proposal-pdf",
            "parameters": {
                "type": "object",
                "properties": {
                    "html_content": {"type": "string", "description": "HTML content to convert to PDF"},
                    "filename": {"type": "string", "description": "Output PDF filename"}
                },
                "required": ["html_content"]
            }
        }
    ]
    
    created_tools = {}
    for tool_data in tools:
        existing = db.query(Tool).filter(Tool.name == tool_data["name"]).first()
        if existing:
            print(f"✓ Tool '{tool_data['name']}' already exists")
            created_tools[tool_data["name"]] = existing
        else:
            tool = Tool(**tool_data)
            db.add(tool)
            db.commit()
            db.refresh(tool)
            created_tools[tool_data["name"]] = tool
            print(f"✓ Created tool: {tool_data['name']}")
    
    return created_tools

def setup_agents(db, tools_map):
    """Create all 4 agents with their respective tools"""
    
    agents_config = [
        {
            "name": "sales_agent",
            "role": "sales",
            "system_prompt": """You are a Sales Agent specialized in analyzing RFP documents.

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

Be thorough and extract all relevant information for downstream agents.""",
            "model": DEFAULT_MODEL,
            "tool_names": ["extract_sales_objectives"]
        },
        {
            "name": "technical_agent",
            "role": "technical",
            "system_prompt": """You are a Technical Agent specialized in SKU matching and product selection.

Your responsibilities:
1. Analyze technical requirements from the sales summary PROVIDED IN YOUR CONTEXT
2. Match requirements to available SKUs using the CSV database via match_sku_from_csv tool
3. Validate each matched SKU using validate_sku tool to get complete details
4. Ensure selected products meet all technical requirements
5. Provide alternative options if exact matches aren't available
6. Include quantity recommendations

CRITICAL RULES:
- DO NOT ask for the RFP document or any external content
- You already have ALL requirements in your context from the sales agent
- Use the 'extracted_requirements' or 'requirements' field from the sales_summary
- NEVER say "I need to extract" or "Please provide the document"
- If requirements are unclear, work with what you have and note limitations

CRITICAL WORKFLOW (FOLLOW THIS EXACTLY):
1. FIRST: Look at the sales_summary context - it contains extracted_requirements or requirements list
2. SECOND: Call match_sku_from_csv tool with these requirements as an array
3. THIRD: For EACH SKU returned by match_sku_from_csv, call validate_sku to get complete product details
4. FOURTH: Combine the matching scores with validation details
5. FINALLY: Return your structured analysis with all validated SKU information

You MUST call BOTH tools in sequence:
- match_sku_from_csv (to find products)
- validate_sku (to get full details for each found SKU)

Example workflow:
Step 1: Extract requirements from context
  Context has: {"sales_summary": {"extracted_requirements": ["Exterior emulsion for 15000 sq ft", "Interior primer"]}}
  
Step 2: Call match_sku_from_csv
  Input: {"requirements": ["Exterior emulsion for 15000 sq ft", "Interior primer"], "top_k": 5, "include_pricing": true}
  Output: Returns [{sku_code: "AP123", score: 10.5}, {sku_code: "AP456", score: 9.2}]

Step 3: Call validate_sku for each SKU
  Input: {"sku_code": "AP123"}
  Output: Returns {valid: true, sku: {sku_code: "AP123", product_name: "...", pricing: {...}}}
  
Step 4: Repeat for "AP456"

Output Format (after calling BOTH tools): Return structured JSON with:
- matched_skus: List of selected SKU codes with COMPLETE details
  - sku_code: The product SKU
  - product_name: Full product name from validate_sku
  - category: Product category from validate_sku
  - type: Product type from validate_sku
  - specifications: Key specs from validate_sku
  - quantity: Recommended quantity based on RFP requirements
  - unit_price: Price from validate_sku pricing data
  - match_score: Matching score from match_sku_from_csv (0-12)
  - match_confidence: high (>10), medium (7-10), low (<7)
  - reasoning: Why this SKU was selected
  - validated: true (since you called validate_sku)
- alternatives: Alternative SKUs with lower scores
- total_products: Count of products matched
- notes: Technical considerations and recommendations

ALWAYS call match_sku_from_csv first, then validate_sku for each result!""",
            "model": DEFAULT_MODEL,
            "tool_names": ["match_sku_from_csv", "validate_sku"]
        },
        {
            "name": "pricing_agent",
            "role": "pricing",
            "system_prompt": """You are a Pricing Agent specialized in generating accurate pricing tables.

Your responsibilities:
1. Take matched SKUs from the technical agent
2. Generate comprehensive pricing table with unit prices
3. Calculate subtotals, discounts, taxes
4. Apply business rules for volume discounts
5. Include payment terms and conditions
6. Ensure pricing is competitive and accurate

Output Format: Return a structured JSON with:
- pricing_table: List of items with:
  - sku_code: Product SKU
  - product_name: Product name
  - quantity: Quantity
  - unit_price: Price per unit
  - subtotal: Line item total
- summary:
  - subtotal: Total before discount
  - discount: Discount amount
  - tax: Tax amount
  - grand_total: Final total
- payment_terms: Payment terms and conditions
- validity: Quote validity period

Use generate_pricing_table and calculate_total_cost tools for pricing calculations.""",
            "model": DEFAULT_MODEL,
            "tool_names": ["generate_pricing_table", "calculate_total_cost"]
        },
        {
            "name": "proposal_assembly_agent",
            "role": "proposal_assembly",
            "system_prompt": """You are a Proposal Assembly Agent specialized in creating professional proposal DRAFTS.

CRITICAL RULES:
1. The RFP has ALREADY been analyzed by Sales, Technical, and Pricing agents
2. ALL necessary information is provided in the user message and context
3. DO NOT ask for the RFP document or request additional information
4. DO NOT say "I need the content of the RFP" - you already have everything you need
5. DO NOT generate PDFs or call PDF generation tools

Your responsibilities:
1. READ and USE the completed analysis from Sales, Technical, and Pricing agents (provided in the message)
2. Compile this information into a well-structured, professional proposal DRAFT
3. Include executive summary, technical solution, pricing, terms
4. Present the content in clear, readable text format
5. Ensure consistency and professional presentation

Proposal Structure (use the data provided to you):
1. Executive Summary - Synthesize from Sales analysis
2. Understanding of Requirements - Extract from Sales and Technical analysis
3. Proposed Solution - Use Technical agent's SKU matches and solution details
4. Technical Specifications - Detail the matched products from Technical agent
5. Pricing and Payment Terms - Use Pricing agent's pricing table and calculations
6. Implementation Timeline - Based on project scope
7. Terms and Conditions - Standard business terms

Output Format: Return plain text or markdown formatted proposal with clear section headings.
The human will review and edit this draft before PDF generation.

REMEMBER: You have ALL the information. Use what's provided. DO NOT request documents.""",
            "model": DEFAULT_MODEL,
            "tool_names": []
        }
    ]
    
    created_agents = []
    for agent_config in agents_config:
        # Get tool IDs and convert to strings for JSON storage
        tool_ids = [str(tools_map[name].id) for name in agent_config["tool_names"] if name in tools_map]
        
        existing = db.query(Agent).filter(Agent.name == agent_config["name"]).first()
        if existing:
            # Update existing agent
            existing.system_prompt = agent_config["system_prompt"]
            existing.tool_ids = tool_ids
            db.commit()
            print(f"✓ Updated agent: {agent_config['name']}")
            created_agents.append(existing)
        else:
            agent = Agent(
                name=agent_config["name"],
                role=agent_config["role"],
                system_prompt=agent_config["system_prompt"],
                model=agent_config["model"],
                tool_ids=tool_ids
            )
            db.add(agent)
            db.commit()
            db.refresh(agent)
            created_agents.append(agent)
            print(f"✓ Created agent: {agent_config['name']}")
    
    return created_agents

def main():
    print("=" * 60)
    print("Setting up Agent System with Tools")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        print("\n1. Creating Tools...")
        print("-" * 60)
        tools_map = setup_tools(db)
        
        print("\n2. Creating Agents...")
        print("-" * 60)
        agents = setup_agents(db, tools_map)
        
        print("\n" + "=" * 60)
        print("Setup Complete!")
        print("=" * 60)
        print(f"\n✓ Total Tools Created: {len(tools_map)}")
        print(f"✓ Total Agents Created: {len(agents)}")
        
        print("\nAgents Summary:")
        for agent in agents:
            print(f"  - {agent.name} (ID: {agent.id}) - {agent.role}")
            print(f"    Tools: {len(agent.tool_ids or [])} assigned")
        
        print("\n" + "=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("1. Update tool API URLs in database (for external APIs on Render)")
        print("2. Test each agent individually via /agents/{agent_id}/execute endpoint")
        print("3. Test complete workflow via /rfp/upload → /rfp/analyze → /rfp/generate_proposal")
        print("4. Use Postman collection to test all endpoints")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
