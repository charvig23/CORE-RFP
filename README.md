# EY Techathon 6.0 - Multi-Agent RFP Orchestration Platform

A full-stack RFP automation system that reads an uploaded requirement document, routes it through specialized AI agents, fetches SKU and pricing data, and produces a proposal draft for human approval.

The repo has three main parts:
- `C.O.R.E/` - React frontend on port `3000`
- `agentSystem/` - FastAPI orchestration API on port `8000`
- `BackendCodes/` - Flask SKU / pricing / PDF tool service on port `8080`

## What This Project Does

- Uploads RFPs as PDF or text
- Extracts sales requirements and project scope
- Matches technical SKUs from CSV datasets
- Generates pricing tables and proposal content
- Supports human approval before final PDF generation
- Stores workflow state and execution history in the database

## System Architecture

```mermaid
flowchart LR
    U[User] --> B[Browser]
    B --> FE[React UI<br/>localhost:3000]
    FE --> API[FastAPI Orchestrator<br/>localhost:8000]
    API --> DB[(Supabase Postgres)]
    API --> LLM[Google Gemini]
    API --> TOOLS[Flask Tool Service<br/>localhost:8080]
    TOOLS --> CSV[SKU / Pricing CSV Files]
    TOOLS --> PDF[PDF Generation]
    API --> FE
```

## End-to-End Workflow

```mermaid
sequenceDiagram
    participant User
    participant UI as React UI :3000
    participant API as FastAPI :8000
    participant Tool as Flask Tools :8080
    participant DB as Supabase Postgres
    participant LLM as Gemini

    User->>UI: Upload RFP / start workflow
    UI->>API: POST RFP or trigger analysis
    API->>DB: Save RFP + progress
    API->>LLM: Route to sales / technical / pricing / proposal agents
    API->>Tool: Match SKU / validate SKU / build PDF
    Tool-->>API: Return matches / PDF result
    API->>DB: Store agent outputs and final status
    API-->>UI: Return status, draft, proposal, links
```

## Service Map

| Service | Port | Role |
|---|---:|---|
| React frontend | 3000 | UI for uploads, workflow, approval, and results |
| FastAPI backend | 8000 | Main API, database layer, agent orchestration |
| Flask tool service | 8080 | SKU matching, validation, pricing, PDF helpers |
| Supabase Postgres | N/A | Persistent storage for agents, RFPs, logs, and proposals |

## Repository Layout

```text
R2/
  C.O.R.E/         React app
  agentSystem/     FastAPI app, agent logic, database models, docs
  BackendCodes/    Flask SKU and PDF service
  *.md             Architecture, workflow, and implementation guides
```

## Quick Start

### 1. Install prerequisites
- Python 3.11+
- Node.js 18+
- A Supabase project
- A Google Gemini API key

### 2. Configure environment
Create `agentSystem/.env`:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
GOOGLE_API_KEY=your_google_api_key_here
```

If Supabase is unavailable, the backend falls back to a local SQLite database for development.

### 3. Install backend dependencies

```powershell
cd agentSystem
pip install -r requirements.txt
cd ..\BackendCodes
pip install -r requirements_flask.txt
```

### 4. Seed the database

```powershell
cd ..\agentSystem
python setup_agents.py
```

### 5. Start the Flask tools service

```powershell
cd ..\BackendCodes
python sku_matching_api.py
```

### 6. Start the FastAPI backend

```powershell
cd ..\agentSystem
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### 7. Start the frontend

```powershell
cd ..\C.O.R.E
npm install
npm start
```

## How The Pipeline Works

1. The user opens the React UI in the browser at `http://localhost:3000`.
2. The frontend sends API calls to FastAPI at `http://localhost:8000`.
3. FastAPI saves and reads workflow state from Supabase Postgres.
4. FastAPI routes the request through Sales, Technical, Pricing, and Proposal agents.
5. When SKU matching or PDF generation is needed, FastAPI calls the Flask service at `http://localhost:8080`.
6. The Flask service reads local CSV data, produces matching results, and returns JSON.
7. FastAPI returns the merged result to the frontend.
8. The user reviews the proposal draft and can approve it for final PDF generation.

## Main Features

- Multi-agent orchestration with Gemini
- SKU matching from CSV files
- Proposal draft generation
- Human-in-the-loop approval flow
- Execution history and progress tracking
- PDF generation support
- Supabase-backed persistence with local fallback for development

## Agent Roles

| Agent | Responsibility |
|---|---|
| Sales Agent | Extracts requirements, objectives, scope, and timeline from the RFP |
| Technical Agent | Converts requirements into SKU matches and validates technical fit |
| Pricing Agent | Builds pricing tables and cost breakdowns |
| Proposal Assembly Agent | Combines all outputs into the final proposal draft |

## Environment Variables

| Variable | Used By | Purpose |
|---|---|---|
| `DATABASE_URL` | Backend | Supabase Postgres connection string |
| `GOOGLE_API_KEY` | Backend | Gemini API access |
| `REACT_APP_API_BASE` | Frontend | Override FastAPI base URL if needed |
| `REACT_APP_TOOLS_BASE` | Frontend | Override Flask tools base URL if needed |
| `SKU_CSV_PATH` | Flask tools | Custom SKU CSV file location |
| `PRICING_CSV_PATH` | Flask tools | Custom pricing CSV file location |

## Testing Checklist

- Open `http://127.0.0.1:8000/docs`
- Check `GET /agents/list`
- Check `GET /tools/list`
- Open `http://127.0.0.1:8080/api/health`
- Run `python test_sku_api.py` in `BackendCodes/`
- Upload an RFP from the frontend and verify the workflow status updates

## Database Notes

- Primary storage is Supabase Postgres
- Tables are created automatically on startup
- Local SQLite is only a fallback when the database connection fails
- RFP uploads are stored on the backend filesystem under `agentSystem/uploads`

## Further Reading

- `ARCHITECTURE_DIAGRAM.md`
- `WORKFLOW_IMPLEMENTATION_GUIDE.md`
- `FRONTEND_INTEGRATION_GUIDE.md`
- `RFP_UPLOAD_GUIDE.md`
- `SKU_MATCHING_GUIDE.md`
- `PROGRESS_TRACKING_GUIDE.md`
- `agentSystem/README.md`
- `agentSystem/API_GUIDE.md`

## GitHub Upload

If you are publishing this to a new GitHub repository, keep the root of this folder as the repo root, then add the files from this directory only.
