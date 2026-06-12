# 🔄 Step-by-Step Agent Workflow with HITL - Implementation Guide

## Overview

This feature implements a **step-by-step agent execution workflow** with **Human-in-the-Loop (HITL) approval** between each agent. After every agent executes, the system:
1. Shows the output
2. Asks the human if they want to continue
3. Proceeds to next agent only if approved
4. Stops and returns results if rejected

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   React Frontend (C.O.R.E)                  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │          AgentWorkflow Component                    │    │
│  │                                                      │    │
│  │  1. Select RFP                                      │    │
│  │  2. Show Agent Pipeline                             │    │
│  │  3. Execute Agent → Show Output                     │    │
│  │  4. HITL Approval Dialog                            │    │
│  │  5. Continue or Stop                                │    │
│  └────────────────────────────────────────────────────┘    │
│                         ↓                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓ HTTP POST
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (agentSystem)                   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │        Workflow Router (/workflow/*)                │    │
│  │                                                      │    │
│  │  POST /execute-step                                 │    │
│  │   - Takes: rfp_id, step_index, context             │    │
│  │   - Calls: AgentOrchestrator                       │    │
│  │   - Returns: Agent output + next step info         │    │
│  │                                                      │    │
│  │  GET /pipeline                                      │    │
│  │   - Returns: Agent pipeline configuration          │    │
│  │                                                      │    │
│  │  GET /{rfp_id}/current-state                       │    │
│  │   - Returns: Current workflow progress             │    │
│  └────────────────────────────────────────────────────┘    │
│                         ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Agent Orchestrator                        │    │
│  │                                                      │    │
│  │  - Loads agent from database                       │    │
│  │  - Loads agent's tools                             │    │
│  │  - Executes agent with GPT-4                       │    │
│  │  - Handles tool calls (API/function)               │    │
│  │  - Returns structured output                        │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          ↓ (For Technical Agent)
┌─────────────────────────────────────────────────────────────┐
│           Flask SKU Matching API (BackendCodes)             │
│                                                              │
│  POST /api/match-sku                                        │
│   - Fuzzy match products to requirements                   │
│   - Return ranked SKU matches with pricing                 │
└─────────────────────────────────────────────────────────────┘
```

## Agent Pipeline

The workflow executes agents in this order:

1. **Sales Agent** - Extracts requirements and objectives from RFP
2. **Technical Agent** - Matches SKUs using `match_sku_from_csv` tool
3. **Pricing Agent** - Generates pricing table
4. **Proposal Assembly Agent** - Creates final proposal document

## Files Created/Modified

### Backend (agentSystem/)

#### New Files:
1. **`routers/workflow.py`** - Workflow orchestration endpoints
   - `POST /workflow/execute-step` - Execute single agent step
   - `GET /workflow/pipeline` - Get agent pipeline config
   - `GET /workflow/{rfp_id}/current-state` - Get workflow progress

#### Modified Files:
1. **`app.py`**
   - Added CORS middleware for React frontend
   - Registered workflow router

2. **`schemas.py`**
   - Added `StepExecutionRequest` schema
   - Added `StepExecutionResponse` schema

### Frontend (C.O.R.E/)

#### New Files:
1. **`src/components/AgentWorkflow.jsx`** - Main workflow component
   - RFP selection interface
   - Pipeline progress visualization
   - Step-by-step execution
   - HITL approval dialog
   - Execution history display

2. **`src/components/AgentWorkflow.css`** - Component styling

#### Modified Files:
1. **`src/services/api.js`**
   - Added `executeWorkflowStep()` function
   - Added `getWorkflowPipeline()` function
   - Added `getWorkflowState()` function

2. **`src/pages/ControlCenter.jsx`**
   - Added tab navigation
   - Integrated AgentWorkflow component
   - Kept demo mode for reference

3. **`src/App.css`**
   - Added tab navigation styles

## How It Works

### Frontend Flow

```javascript
// 1. User selects RFP
selectRfp(rfp) → fetch current state → display progress

// 2. User clicks "Execute Agent"
executeStep() → POST /workflow/execute-step
  {
    rfp_id: 1,
    step_index: 0,  // Sales Agent
    context: {}
  }

// 3. Backend executes agent and returns output
Response: {
  agent_name: "Sales Agent",
  output: {...},
  has_next_step: true,
  next_agent: {...},
  current_context: {...}
}

// 4. Show approval dialog
"Agent complete. Continue to next agent?"
  [Approve] → setCurrentStep(currentStep + 1) → executeStep()
  [Reject] → Stop workflow

// 5. Context accumulates across agents
Context after Sales: { sales_summary: {...} }
Context after Technical: { sales_summary: {...}, technical_matches: {...} }
Context after Pricing: { sales_summary: {...}, technical_matches: {...}, pricing_data: {...} }
```

### Backend Flow

```python
# 1. Receive execution request
@router.post("/execute-step")
def execute_workflow_step(request):
    rfp = db.query(RFP).filter_by(id=request.rfp_id).first()
    agent_config = AGENT_PIPELINE[request.step_index]
    
    # 2. Prepare message based on agent type
    if step_index == 0:  # Sales
        message = f"Analyze RFP: {rfp.content}"
        context = None
    elif step_index == 1:  # Technical
        message = "Match SKUs based on sales summary"
        context = request.context  # Has sales_summary
    
    # 3. Execute agent through orchestrator
    result = orchestrator.run_specific_agent(
        agent_config["name"],
        message,
        rfp_id=request.rfp_id,
        context=context
    )
    
    # 4. Update RFP with output
    rfp.sales_summary = result  # or technical_matches, etc.
    db.commit()
    
    # 5. Return output with next step info
    return {
        "output": result,
        "has_next_step": step_index < 3,
        "next_agent": AGENT_PIPELINE[step_index + 1],
        "current_context": {**context, sales_summary: result}
    }
```

### Tool Execution (Technical Agent Example)

```python
# Agent decides to use tool
tool_call = {
    "name": "match_sku_from_csv",
    "arguments": {
        "requirements": [
            "Exterior emulsion paint",
            "Interior primer"
        ],
        "top_k": 3
    }
}

# Orchestrator executes tool
def execute_tool(tool_name, parameters):
    tool = db.query(Tool).filter_by(name=tool_name).first()
    
    if tool.tool_type == "api":
        # Call Flask API
        response = requests.post(
            tool.code,  # http://localhost:8080/api/match-sku
            json=parameters
        )
        return response.json()

# Tool result returned to agent
{
    "matches": [
        {
            "requirement": "Exterior emulsion paint",
            "matches": [
                {
                    "sku": "SKU001",
                    "product_name": "Premium Exterior Emulsion",
                    "score": 0.92,
                    "price": 399.99
                }
            ]
        }
    ]
}

# Agent formats final response
"I found matching products: SKU001 (Premium Exterior Emulsion - ₹399.99)..."
```

## Usage Instructions

### 1. Start All Services

**Terminal 1 - Flask SKU API:**
```bash
cd BackendCodes
python sku_matching_api.py
```

**Terminal 2 - FastAPI Backend:**
```bash
cd agentSystem
uvicorn app:app --reload --port 8000
```

**Terminal 3 - React Frontend:**
```bash
cd C.O.R.E
npm start
```

### 2. Access the Application

Open http://localhost:3000

### 3. Use the Workflow

1. **Switch to "Agent Workflow (Live)" tab**
2. **Select an RFP** from the list
3. **View the pipeline** - Shows all 4 agents
4. **Click "Execute Sales Agent"**
   - Agent analyzes RFP
   - Extracts requirements and objectives
   - Output displayed
5. **Approval Dialog appears**
   - Review Sales Agent output
   - Click "Approve & Continue" or "Stop Here"
6. **If approved, Technical Agent executes**
   - Uses `match_sku_from_csv` tool
   - Calls Flask API
   - Matches products to requirements
   - Returns SKU matches with pricing
7. **Continue through Pricing and Proposal agents**
8. **Workflow completes** - All outputs saved to RFP

### 4. Review Results

- **Execution History** - Shows all agent outputs
- **Current State** - Tracks progress through pipeline
- **Final Proposal** - Complete document when finished

## API Endpoints

### Execute Step
```http
POST /workflow/execute-step
Content-Type: application/json

{
  "rfp_id": 1,
  "step_index": 0,
  "context": {}
}

Response:
{
  "rfp_id": 1,
  "step_index": 0,
  "agent_name": "Sales Agent",
  "status": "success",
  "output": {
    "agent_name": "sales_agent",
    "response": "...",
    "tool_calls": []
  },
  "has_next_step": true,
  "next_agent": {
    "name": "technical_agent",
    "display": "Technical Agent",
    "description": "Match SKUs and products"
  },
  "current_context": {
    "sales_summary": {...}
  }
}
```

### Get Pipeline
```http
GET /workflow/pipeline

Response:
{
  "total_steps": 4,
  "pipeline": [
    {
      "name": "sales_agent",
      "display": "Sales Agent",
      "description": "Extract requirements and objectives"
    },
    ...
  ]
}
```

### Get Workflow State
```http
GET /workflow/{rfp_id}/current-state

Response:
{
  "rfp_id": 1,
  "current_step": 2,
  "completed_steps": 2,
  "total_steps": 4,
  "status": "analyzing",
  "outputs": {
    "sales_summary": {...},
    "technical_matches": {...},
    "pricing_data": null,
    "final_proposal": null
  }
}
```

## Features

### ✅ Implemented

- [x] Step-by-step agent execution
- [x] Human-in-the-loop approval
- [x] Visual pipeline progress
- [x] Context accumulation across agents
- [x] Tool execution (API and function types)
- [x] Execution history display
- [x] Workflow state persistence
- [x] Error handling
- [x] Responsive UI design

### 🎨 UI Features

- Visual pipeline with progress indicators
- Animated active step
- Color-coded status (pending/active/completed)
- Expandable output previews
- Approval/rejection buttons
- Execution timestamps
- Completion celebration

## Benefits

1. **Human Control** - Approve each step before proceeding
2. **Transparency** - See exactly what each agent produces
3. **Flexibility** - Stop at any point and review
4. **Context Preservation** - Each agent builds on previous outputs
5. **Tool Integration** - Seamlessly calls external APIs
6. **Error Recovery** - Stop if something goes wrong
7. **Audit Trail** - Complete history of all executions

## Testing

### Test Full Workflow

1. Upload an RFP via `/rfp/upload` endpoint
2. Select it in the UI
3. Execute each agent step by step
4. Verify:
   - Sales Agent extracts requirements
   - Technical Agent calls SKU matching tool
   - Pricing Agent generates pricing
   - Proposal Agent creates final document

### Test HITL Approval

1. Execute Sales Agent
2. Click "Stop Here" instead of approve
3. Verify workflow stops
4. No subsequent agents execute
5. Results saved up to current step

### Test Tool Execution

1. Execute Technical Agent
2. Verify it calls Flask API at `http://localhost:8080/api/match-sku`
3. Check network tab for API request
4. Verify SKU matches returned to agent
5. Agent formats results properly

## Troubleshooting

### Agent Not Using Tool

**Problem:** Technical Agent doesn't call SKU matching tool

**Solution:**
```bash
cd agentSystem
python setup_agents.py  # Re-register tools
```

### CORS Error

**Problem:** Frontend can't call backend

**Solution:** Verify CORS is enabled in `app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Flask API Not Reachable

**Problem:** Tool execution fails

**Solution:**
1. Check Flask is running: `curl http://localhost:8080/api/health`
2. Verify URL in tool configuration
3. Check network connectivity

## Architecture Benefits

### Separation of Concerns

- **Backend (agentSystem):** Agent orchestration, tool execution, database
- **Backend (BackendCodes):** SKU matching logic, CSV processing
- **Frontend (C.O.R.E):** UI, user interaction, visualization

### Independent Deployment

Each component can be:
- Developed separately
- Deployed independently
- Scaled individually
- Tested in isolation

### Future Extensions

Easy to add:
- More agents to pipeline
- More tools per agent
- Custom approval logic
- Workflow branching
- Parallel agent execution
- Workflow templates

## Next Steps

1. ✅ Test the complete workflow end-to-end
2. 🔲 Add real RFP data
3. 🔲 Customize agent prompts
4. 🔲 Add more tools
5. 🔲 Deploy to production
6. 🔲 Add authentication
7. 🔲 Add workflow analytics

---

**You're all set!** Start all three services and begin processing RFPs with step-by-step agent execution! 🚀
