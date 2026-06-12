# Agent System API Guide

## Overview
This system orchestrates 4 specialized AI agents for RFP processing:
1. **Sales Agent** - Extracts requirements and objectives
2. **Technical Agent** - Matches SKUs from CSV
3. **Pricing Agent** - Generates pricing tables
4. **Proposal Assembly Agent** - Creates final proposal

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create `.env` file:
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.yuibfeewjjqowirbfaqr.supabase.co:5432/postgres
GOOGLE_API_KEY=your_google_api_key_here
```

To switch to your new Supabase project, replace the `DATABASE_URL` value with that project’s Postgres URI from the Supabase dashboard.

`DATABASE_URL` is optional for local development. If Supabase is paused or unreachable, the app will automatically use a local SQLite database in `%TEMP%\ey_agent_system.db`.

### 3. Initialize Database and Agents
```bash
python setup_agents.py
```

This seeds the configured database with 7 tools and 4 agents. If the remote database is unavailable, it seeds the local SQLite fallback instead.

### 4. Run the Server
```bash
uvicorn app:app --reload
```

Server will start at: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

---

## API Endpoints

### 🔧 Tool Management

#### 1. Create Tool
```http
POST /tools/create
Content-Type: application/json

{
  "name": "match_sku_from_csv",
  "description": "Match SKUs from CSV based on requirements",
  "code": "https://your-render-service.onrender.com/api/match-sku",
  "tool_type": "api",
  "parameters": {
    "type": "object",
    "properties": {
      "requirements": {
        "type": "array",
        "items": {"type": "string"}
      }
    },
    "required": ["requirements"]
  }
}
```

#### 2. List All Tools
```http
GET /tools/list
```

#### 3. Get Tool by ID
```http
GET /tools/{tool_id}
```

#### 4. Update Tool
```http
PUT /tools/{tool_id}
Content-Type: application/json

{
  "description": "Updated description",
  "code": "https://new-url.onrender.com/api/endpoint"
}
```

#### 5. Delete Tool
```http
DELETE /tools/{tool_id}
```

---

### 🤖 Agent Management

#### 1. Create Agent
```http
POST /agents/create
Content-Type: application/json

{
  "name": "sales_agent",
  "role": "sales",
  "system_prompt": "You are a sales agent...",
  "model": "gemini-2.5-flash",
  "tool_ids": [1, 2]
}
```

#### 2. List All Agents
```http
GET /agents/list
```

#### 3. Get Agent by ID
```http
GET /agents/{agent_id}
```

#### 4. Update Agent
```http
PUT /agents/{agent_id}
Content-Type: application/json

{
  "system_prompt": "Updated prompt",
  "tool_ids": [1, 2, 3]
}
```

#### 5. Assign Tools to Agent
```http
POST /agents/{agent_id}/add-tools
Content-Type: application/json

{
  "tool_ids": [1, 2, 3]
}
```

#### 6. Execute Agent
```http
POST /agents/{agent_id}/execute
Content-Type: application/json

{
  "agent_name": "sales_agent",
  "message": "Analyze this RFP...",
  "context": {"key": "value"}
}
```

#### 7. Delete Agent
```http
DELETE /agents/{agent_id}
```

---

### 📄 RFP Processing

#### 1. Upload RFP (Text)
```http
POST /rfp/upload
Content-Type: application/json

{
  "title": "Enterprise Software RFP",
  "content": "We need a comprehensive software solution..."
}
```

**Response:**
```json
{
  "id": 1,
  "title": "Enterprise Software RFP",
  "status": "uploaded",
  "created_at": "2025-12-06T10:00:00"
}
```

#### 2. Upload RFP (PDF File)
```http
POST /rfp/upload-file
Content-Type: multipart/form-data

file: [Select PDF file]
```

**Response:**
```json
{
  "status": "File uploaded",
  "rfp_id": 1,
  "filename": "rfp_document.pdf",
  "text_length": 5432
}
```

#### 3. Analyze RFP
```http
POST /rfp/analyze
Content-Type: application/json

{
  "title": "Enterprise Software RFP",
  "content": "We need a comprehensive software solution..."
}
```

**Response:**
```json
{
  "rfp_id": 1,
  "sales_summary": {
    "objectives": ["Implement CRM", "Integrate with ERP"],
    "requirements": ["Cloud-based", "Mobile support"],
    "budget_info": "$100,000"
  },
  "technical_matches": {
    "matched_skus": [
      {
        "sku_code": "CRM-001",
        "product_name": "Enterprise CRM",
        "quantity": 1
      }
    ]
  }
}
```

#### 4. Generate Proposal
```http
POST /rfp/generate_proposal?rfp_id=1
```

**Response:**
```json
{
  "rfp_id": 1,
  "status": "Proposal generated successfully",
  "proposal": "<html>...</html>",
  "format": "HTML"
}
```

#### 5. Get RFP Status
```http
GET /rfp/{rfp_id}/status
```

**Response:**
```json
{
  "rfp_id": 1,
  "status": "completed",
  "executions": [
    {
      "agent_id": 1,
      "status": "completed",
      "created_at": "2025-12-06T10:00:00"
    }
  ]
}
```

#### 6. Get Final Proposal
```http
GET /rfp/{rfp_id}/proposal
```

**Response:**
```json
{
  "rfp_id": 1,
  "title": "Enterprise Software RFP",
  "proposal": "<html>...</html>",
  "sales_summary": {...},
  "technical_matches": {...},
  "pricing_data": {...}
}
```

#### 7. List All RFPs
```http
GET /rfp/list
```

#### 8. Get RFP by ID
```http
GET /rfp/{rfp_id}
```

#### 9. Delete RFP
```http
DELETE /rfp/{rfp_id}
```

---

## Complete Workflow Example

### Step 1: Upload RFP
```bash
curl -X POST "http://localhost:8000/rfp/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Cloud Infrastructure RFP",
    "content": "We need cloud infrastructure for 1000 users..."
  }'
```

**Response:** Get `rfp_id`

### Step 2: Analyze RFP
```bash
curl -X POST "http://localhost:8000/rfp/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Cloud Infrastructure RFP",
    "content": "We need cloud infrastructure for 1000 users..."
  }'
```

**Response:** Get analysis with sales summary and technical matches

### Step 3: Generate Proposal
```bash
curl -X POST "http://localhost:8000/rfp/generate_proposal?rfp_id=1"
```

**Response:** Complete HTML proposal

---

## Agent Workflow Sequence

```
User Upload RFP
    ↓
[Sales Agent]
  → Extracts objectives, requirements, scope
  → Uses: extract_sales_objectives tool
  → Output: sales_summary (JSON)
    ↓
[Technical Agent]
  → Matches SKUs from CSV
  → Uses: match_sku_from_csv, validate_sku tools
  → Input: sales_summary
  → Output: technical_matches (JSON)
    ↓
[Pricing Agent]
  → Generates pricing table
  → Uses: generate_pricing_table, calculate_total_cost tools
  → Input: technical_matches
  → Output: pricing_data (JSON)
    ↓
[Proposal Assembly Agent]
  → Creates final proposal
  → Uses: format_proposal_html, generate_pdf_proposal tools
  → Input: All previous outputs
  → Output: final_proposal (HTML/PDF)
```

---

## Tool Deployment on Render

For external API tools (deployed separately on Render):

### Example: SKU Matching Service
```python
# Deploy this on Render
from fastapi import FastAPI
import pandas as pd

app = FastAPI()

@app.post("/api/match-sku")
def match_sku(requirements: list, csv_file_url: str = None):
    # Load CSV with SKU data
    df = pd.read_csv("sku_database.csv")
    
    # Match logic
    matched = []
    for req in requirements:
        # Match SKUs based on requirement
        matches = df[df['description'].str.contains(req, case=False)]
        matched.extend(matches.to_dict('records'))
    
    return {"matched_skus": matched}
```

Update tool in database:
```http
PUT /tools/{tool_id}
{
  "code": "https://your-sku-service.onrender.com/api/match-sku"
}
```

---

## Testing with Postman

1. **Import Collection**: Use `postman_collection.json`
2. **Set Environment Variables**:
   - `base_url`: `http://localhost:8000`
   - `rfp_id`: (will be set after upload)
3. **Run Collection** in order:
   - Setup → Create Tools
   - Setup → Create Agents
   - RFP → Upload
   - RFP → Analyze
   - RFP → Generate Proposal

---

## Database Schema

### Tables:
- **tools** - Tool definitions (functions/APIs)
- **agents** - Agent configurations with system prompts
- **rfps** - RFP documents and processing results
- **conversations** - Agent conversation history
- **agent_executions** - Execution logs for tracking

---

## Error Handling

All endpoints return standard error responses:

```json
{
  "detail": "Error message here"
}
```

Common status codes:
- `200` - Success
- `404` - Resource not found
- `400` - Bad request
- `500` - Server error

---

## Next Steps

1. ✅ Run `setup_agents.py` to create agents
2. ✅ Update tool URLs after deploying to Render
3. ✅ Test individual agents via `/agents/{agent_id}/execute`
4. ✅ Test complete workflow via RFP endpoints
5. ✅ Monitor executions via `/rfp/{id}/status`
6. ✅ Export proposals via `/rfp/{id}/proposal`

---

## Support

For issues or questions:
- Check API docs: `http://localhost:8000/docs`
- Review logs in terminal
- Check database tables for data
