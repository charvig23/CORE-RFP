"""
Example setup script to initialize agents and tools
Run this to populate your database with sample agents and tools
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Step 1: Create Tools
print("Creating tools...")

# Tool 1: Extract text from PDF
pdf_extractor_tool = {
    "name": "extract_pdf_text",
    "description": "Extract text content from a PDF file",
    "code": """
def extract_pdf_text(file_path: str) -> str:
    # Placeholder - integrate PyMuPDF or pdfplumber
    return f"Extracted text from {file_path}"
""",
    "tool_type": "function",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to PDF file"}
        },
        "required": ["file_path"]
    }
}

# Tool 2: Match SKU from CSV
sku_matcher_tool = {
    "name": "match_sku",
    "description": "Match product SKUs from a CSV database based on requirements",
    "code": "https://your-render-service.onrender.com/api/match-sku",  # External API
    "tool_type": "api",
    "parameters": {
        "type": "object",
        "properties": {
            "requirements": {"type": "array", "items": {"type": "string"}},
            "csv_path": {"type": "string"}
        },
        "required": ["requirements"]
    }
}

# Tool 3: Generate pricing table
pricing_tool = {
    "name": "generate_pricing",
    "description": "Generate pricing table based on matched SKUs",
    "code": """
def generate_pricing(skus: list, quantities: list) -> dict:
    # Placeholder pricing logic
    pricing_table = []
    for sku, qty in zip(skus, quantities):
        pricing_table.append({
            "sku": sku,
            "quantity": qty,
            "unit_price": 100.0,  # Fetch from database
            "total": qty * 100.0
        })
    return {"pricing_table": pricing_table, "total_cost": sum(item["total"] for item in pricing_table)}
""",
    "tool_type": "function",
    "parameters": {
        "type": "object",
        "properties": {
            "skus": {"type": "array", "items": {"type": "string"}},
            "quantities": {"type": "array", "items": {"type": "number"}}
        },
        "required": ["skus", "quantities"]
    }
}

# Tool 4: Create proposal document
proposal_tool = {
    "name": "create_proposal_document",
    "description": "Generate final proposal document in HTML/PDF format",
    "code": "https://your-render-service.onrender.com/api/generate-proposal",
    "tool_type": "api",
    "parameters": {
        "type": "object",
        "properties": {
            "sales_summary": {"type": "object"},
            "technical_data": {"type": "object"},
            "pricing_data": {"type": "object"}
        },
        "required": ["sales_summary", "technical_data", "pricing_data"]
    }
}

tools = [pdf_extractor_tool, sku_matcher_tool, pricing_tool, proposal_tool]
tool_ids = []

for tool in tools:
    response = requests.post(f"{BASE_URL}/tools/create", json=tool)
    if response.status_code == 200:
        tool_id = response.json()["id"]
        tool_ids.append(tool_id)
        print(f"✓ Created tool: {tool['name']} (ID: {tool_id})")
    else:
        print(f"✗ Failed to create tool: {tool['name']}")
        print(response.text)

# Step 2: Create Agents
print("\nCreating agents...")

# Agent 1: Sales Agent
sales_agent = {
    "name": "Sales Agent",
    "role": "sales",
    "system_prompt": """You are a Sales Analysis Agent. Your role is to:
1. Read and analyze RFP documents
2. Extract key requirements, objectives, and scope
3. Identify customer needs and priorities
4. Summarize sales opportunities
5. Output structured JSON with sales summary and objectives

Be thorough and extract all relevant business requirements.""",
    "model": "gemini-2.5-flash",
    "tool_ids": [tool_ids[0]] if tool_ids else []  # PDF extractor
}

# Agent 2: Technical Agent
technical_agent = {
    "name": "Technical Agent",
    "role": "technical",
    "system_prompt": """You are a Technical Matching Agent. Your role is to:
1. Receive sales requirements from the Sales Agent
2. Match requirements to available SKUs in the product catalog
3. Use the SKU matching tool to find best matches
4. Validate technical specifications
5. Output structured JSON with matched SKUs and specifications

Ensure accurate technical matching based on requirements.""",
    "model": "gemini-2.5-flash",
    "tool_ids": [tool_ids[1]] if len(tool_ids) > 1 else []  # SKU matcher
}

# Agent 3: Pricing Agent
pricing_agent = {
    "name": "Pricing Agent",
    "role": "pricing",
    "system_prompt": """You are a Pricing Analysis Agent. Your role is to:
1. Receive matched SKUs from Technical Agent
2. Calculate pricing for each item
3. Generate comprehensive pricing tables
4. Apply discounts and calculate totals
5. Output structured JSON with complete pricing data

Ensure accurate pricing calculations and clear presentation.""",
    "model": "gemini-2.5-flash",
    "tool_ids": [tool_ids[2]] if len(tool_ids) > 2 else []  # Pricing tool
}

# Agent 4: Proposal Assembly Agent
proposal_agent = {
    "name": "Proposal Assembly Agent",
    "role": "proposal_assembly",
    "system_prompt": """You are a Proposal Assembly Agent. Your role is to:
1. Receive data from Sales, Technical, and Pricing agents
2. Compile all information into a professional proposal
3. Format the proposal document (HTML/PDF)
4. Ensure all sections are complete and well-formatted
5. Output final proposal ready for delivery

Create compelling, professional proposals that address all requirements.""",
    "model": "gemini-2.5-flash",
    "tool_ids": [tool_ids[3]] if len(tool_ids) > 3 else []  # Proposal generator
}

agents = [sales_agent, technical_agent, pricing_agent, proposal_agent]

for agent in agents:
    response = requests.post(f"{BASE_URL}/agents/create", json=agent)
    if response.status_code == 200:
        agent_id = response.json()["id"]
        print(f"✓ Created agent: {agent['name']} (ID: {agent_id})")
    else:
        print(f"✗ Failed to create agent: {agent['name']}")
        print(response.text)

print("\n✅ Setup complete!")
print("\nNext steps:")
print("1. Upload an RFP: POST /rfp/upload")
print("2. Process RFP: POST /rfp/{rfp_id}/analyze")
print("3. Get proposal: GET /rfp/{rfp_id}/proposal")
