# Multi-Agent Orchestration System

A FastAPI-based multi-agent system with LLM orchestration for automated RFP processing. The system uses specialized agents (Sales, Technical, Pricing, Proposal Assembly) that work together to process RFPs from start to finish.

## Features

- **Dynamic Agent Management**: Create, update, and manage multiple specialized agents
- **Tool System**: Define custom tools (Python functions or API endpoints) that agents can use
- **LLM Orchestration**: Automatic agent selection based on task requirements
- **RFP Workflow**: Complete pipeline from upload to final proposal generation
- **Database Tracking**: Full audit trail of agent executions and tool calls

## Architecture

```
RFP Upload → Sales Agent → Technical Agent → Pricing Agent → Proposal Agent → Final Proposal
              ↓              ↓                 ↓               ↓
           PDF Extract    SKU Matching    Pricing Table   Document Gen
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.yuibfeewjjqowirbfaqr.supabase.co:5432/postgres
GOOGLE_API_KEY=your_google_api_key_here
```

To switch to your new Supabase project, replace the `DATABASE_URL` value with that project’s Postgres URI from the Supabase dashboard.

`DATABASE_URL` is optional for local development. If Supabase is paused or unreachable, the app falls back to a local SQLite file at `%TEMP%\ey_agent_system.db`.

### 3. Initialize Database

```bash
python -m uvicorn app:app --reload
```

The database tables will be created automatically on first run, either in Supabase/Postgres or in the local SQLite fallback.

### 4. Setup Agents and Tools

Run the example setup script:

```bash
python example_setup.py
```

This will create:
- 4 sample tools (PDF extraction, SKU matching, pricing, proposal generation)
- 4 specialized agents with system prompts

## API Endpoints

### Tool Management

**Create Tool**
```bash
POST /tools/create
{
  "name": "tool_name",
  "description": "What the tool does",
  "code": "def tool_name(param): return result",  # Python code or API URL
  "tool_type": "function",  # or "api"
  "parameters": {
    "type": "object",
    "properties": {
      "param": {"type": "string"}
    },
    "required": ["param"]
  }
}
```

**List Tools**
```bash
GET /tools/list
```

**Update Tool**
```bash
PUT /tools/{tool_id}
{
  "description": "Updated description",
  "code": "updated code"
}
```

**Delete Tool**
```bash
DELETE /tools/{tool_id}
```

**Execute Tool**
```bash
POST /tools/execute
{
  "tool_id": 1,
  "parameters": {"param": "value"}
}
```

### Agent Management

**Create Agent**
```bash
POST /agents/create
{
  "name": "Sales Agent",
  "role": "sales",
  "system_prompt": "You are a sales analysis agent...",
  "model": "gemini-2.5-flash",
  "tool_ids": [1, 2]
}
```

**List Agents**
```bash
GET /agents/list
```

**Get Agent**
```bash
GET /agents/{agent_id}
```

**Update Agent**
```bash
PUT /agents/{agent_id}
{
  "system_prompt": "Updated prompt",
  "tool_ids": [1, 2, 3]
}
```

**Delete Agent**
```bash
DELETE /agents/{agent_id}
```

**Add Tools to Agent**
```bash
POST /agents/{agent_id}/add-tools
[1, 2, 3]  # Tool IDs to add
```

**Remove Tools from Agent**
```bash
POST /agents/{agent_id}/remove-tools
[2]  # Tool IDs to remove
```

**Execute Specific Agent**
```bash
POST /agents/{agent_id}/execute
{
  "message": "Analyze this requirement",
  "context": {"additional": "data"}
}
```

**Auto-Select and Execute Agent**
```bash
POST /agents/orchestrate
{
  "message": "I need to process an RFP"
}
```

### RFP Processing

**Upload RFP (Text)**
```bash
POST /rfp/upload
{
  "title": "Project XYZ RFP",
  "content": "Full RFP text content..."
}
```

**Upload RFP (File)**
```bash
POST /rfp/upload-file
Content-Type: multipart/form-data
file: [PDF/TXT file]
```

**List RFPs**
```bash
GET /rfp/list
```

**Get RFP**
```bash
GET /rfp/{rfp_id}
```

**Process RFP Through All Agents**
```bash
POST /rfp/{rfp_id}/analyze
```

This will:
1. Run Sales Agent to extract requirements
2. Run Technical Agent to match SKUs
3. Run Pricing Agent to generate pricing
4. Run Proposal Agent to create final document

**Get Processing Status**
```bash
GET /rfp/{rfp_id}/status
```

**Get Final Proposal**
```bash
GET /rfp/{rfp_id}/proposal
```

**Delete RFP**
```bash
DELETE /rfp/{rfp_id}
```

## Example Workflow

### 1. Create Tools

```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# Create SKU matching tool
tool = {
    "name": "match_sku",
    "description": "Match SKUs from product catalog",
    "code": "https://your-service.onrender.com/api/match-sku",
    "tool_type": "api",
    "parameters": {
        "type": "object",
        "properties": {
            "requirements": {"type": "array", "items": {"type": "string"}}
        }
    }
}

response = requests.post(f"{BASE_URL}/tools/create", json=tool)
tool_id = response.json()["id"]
```

### 2. Create Agent

```python
agent = {
    "name": "Technical Agent",
    "role": "technical",
    "system_prompt": "You match technical requirements to SKUs.",
  "model": "gemini-2.5-flash",
    "tool_ids": [tool_id]
}

response = requests.post(f"{BASE_URL}/agents/create", json=agent)
agent_id = response.json()["id"]
```

### 3. Upload and Process RFP

```python
# Upload RFP
rfp = {
    "title": "Cloud Infrastructure RFP",
    "content": "We need cloud servers, storage, and networking..."
}
response = requests.post(f"{BASE_URL}/rfp/upload", json=rfp)
rfp_id = response.json()["id"]

# Process through all agents
requests.post(f"{BASE_URL}/rfp/{rfp_id}/analyze")

# Get final proposal
proposal = requests.get(f"{BASE_URL}/rfp/{rfp_id}/proposal")
print(proposal.json())
```

## Deploying Tools on Render

For tools with `tool_type: "api"`, deploy your tool logic on Render:

1. Create a simple Flask/FastAPI service:

```python
from fastapi import FastAPI
app = FastAPI()

@app.post("/api/match-sku")
def match_sku(requirements: list):
    # Your SKU matching logic
    # Read from CSV, database, etc.
    return {"matched_skus": ["SKU-001", "SKU-002"]}
```

2. Deploy to Render and use the URL in tool `code` field

## Agent Roles

- **sales**: Analyzes RFPs, extracts requirements and objectives
- **technical**: Matches technical requirements to SKUs/products
- **pricing**: Generates pricing tables and cost calculations
- **proposal_assembly**: Compiles final proposal document

## Database Schema

- **tools**: Stores reusable tools (functions/APIs)
- **agents**: Stores agent configurations and prompts
- **rfps**: Stores uploaded RFPs and processing results
- **conversations**: Tracks agent interactions
- **agent_executions**: Audit trail of agent runs

## Testing with Postman

1. Import the API at `http://127.0.0.1:8000/docs`
2. Create tools first
3. Create agents with tool assignments
4. Upload an RFP
5. Process the RFP
6. Get the final proposal

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Preferred PostgreSQL connection string. Falls back to local SQLite if unreachable. |
| `GOOGLE_API_KEY` | Google Gemini API key for LLM |

## Development

```bash
# Run development server
python -m uvicorn app:app --reload

# Access API docs
http://127.0.0.1:8000/docs

# Access alternative docs
http://127.0.0.1:8000/redoc
```

## License

MIT
