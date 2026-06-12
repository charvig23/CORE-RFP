# Intelligent Agent Routing & Tool Execution Guide

## ✅ What Was Implemented

### 1. **Proper Tool Execution**
All agents now properly execute their assigned tools:

#### Sales Agent
- **Tool**: `extract_sales_objectives`
- **What it does**: 
  - Parses RFP text line by line
  - Extracts objectives, requirements, scope, budget, timeline
  - Identifies product keywords (paint, emulsion, primer, coating, etc.)
  - Returns structured JSON with `extracted_requirements` array
- **Workflow**: 
  1. Agent receives RFP content
  2. Calls `extract_sales_objectives(rfp_text="...")`
  3. Tool analyzes and returns structured data
  4. Agent enhances with LLM analysis
  5. Returns comprehensive summary

#### Technical Agent
- **Tools**: `match_sku_from_csv`, `validate_sku`
- **What they do**:
  - `match_sku_from_csv`: Calls Flask API to fuzzy match requirements to SKU database
  - `validate_sku`: Verifies specific SKU exists and gets details
- **Workflow**:
  1. Agent extracts `extracted_requirements` from sales context
  2. Calls `match_sku_from_csv(requirements=[...], top_k=5, include_pricing=true)`
  3. Reviews match scores (0-12 scale)
  4. Optionally validates specific SKUs
  5. Returns selected products with confidence scores

#### Pricing Agent
- **Tools**: `generate_pricing_table`, `calculate_total_cost`
- **Workflow**: Takes matched SKUs and generates pricing with taxes/discounts

#### Proposal Assembly Agent
- **Tools**: `format_proposal_html`, `generate_pdf_proposal`
- **Workflow**: Compiles all data into professional proposal document

### 2. **Intelligent Routing System**

The orchestrator now uses LLM-based intelligent routing instead of fixed pipeline:

#### How It Works
```python
orchestrator.select_next_agent(
    current_agent="sales_agent",
    current_output={...},  # What the agent produced
    context={...}          # Full workflow context
)
```

The LLM analyzes:
- Which agent just executed
- What output it produced
- What data is available in context
- What prerequisites are met
- What the logical next step should be

Returns:
```json
{
  "next_agent": "technical_agent",
  "reasoning": "Sales agent extracted requirements, now need SKU matching",
  "ready": true,
  "prerequisites_missing": []
}
```

#### Benefits
- **Adaptive**: Can skip agents if not needed
- **Smart**: Understands workflow state
- **Flexible**: Not locked into fixed sequence
- **Resilient**: Has fallback to sequential routing

### 3. **Enhanced Debug Logging**

Every step is logged:
```
[DEBUG] Executing agent: sales_agent
[DEBUG] Agent has 1 tools: ['extract_sales_objectives']
[DEBUG] Tool schema added: extract_sales_objectives
[DEBUG] Calling OpenAI with 2 messages and 1 tools
[DEBUG] Agent made 1 tool calls
[DEBUG] Executing tool: extract_sales_objectives with args: {...}
[DEBUG] Tool result: {...}
[DEBUG] Getting final response from LLM
[DEBUG] Agent execution completed successfully
[WORKFLOW] Routing decision: {"next_agent": "technical_agent", ...}
```

## 🚀 How To Test

### Step 1: Start All Services

#### Terminal 1 - FastAPI (Agent System)
```powershell
cd agentSystem
uvicorn app:app --reload
```

#### Terminal 2 - Flask (SKU Matching API)
```powershell
cd BackendCodes
python sku_matching_api.py
```

#### Terminal 3 - React Frontend
```powershell
cd C.O.R.E
npm start
```

### Step 2: Upload RFP

1. Go to http://localhost:3000
2. Click "Upload New RFP"
3. Upload `sample-rfp-commercial-building.txt` (or create new RFP)
4. Wait for success message

### Step 3: Execute Step-by-Step Workflow

#### Execute Sales Agent
1. Select the uploaded RFP
2. Click "Start Sales Agent"
3. Watch terminal for:
   ```
   [DEBUG] Agent made 1 tool calls
   [DEBUG] Executing tool: extract_sales_objectives
   ```
4. Review output - should show:
   - Objectives list
   - Requirements list
   - **extracted_requirements** array (important for next step!)
   - Scope, budget, timeline

5. Click "Approve" to continue

#### Execute Technical Agent
1. Watch terminal for:
   ```
   [DEBUG] Agent has 2 tools: ['match_sku_from_csv', 'validate_sku']
   [DEBUG] Agent made 1 tool calls
   [DEBUG] Executing tool: match_sku_from_csv
   [DEBUG] Tool result: {"matches": [...]}
   ```

2. Flask terminal should show:
   ```
   POST /api/match-sku
   Matched 3 SKUs for requirement: Exterior emulsion for walls
   ```

3. Review output - should show:
   - matched_skus array with SKU codes, names, scores
   - match_confidence (high/medium/low)
   - unit_price for each product
   - alternatives

4. Click "Approve" to continue

#### Execute Pricing Agent
1. Should generate pricing table with totals
2. Click "Approve"

#### Execute Proposal Agent
1. Should create final proposal
2. Workflow complete!

## 🔍 Verification Checklist

### Sales Agent Tool Execution
- [ ] Tool `extract_sales_objectives` is called (check logs)
- [ ] Returns structured JSON with all fields
- [ ] `extracted_requirements` array is populated
- [ ] No HTTP 500 errors

### Technical Agent Tool Execution
- [ ] Tool `match_sku_from_csv` is called (check logs)
- [ ] Flask API receives request on port 8080
- [ ] Returns matched SKUs with scores
- [ ] Agent selects products based on scores
- [ ] No connection errors to Flask API

### Intelligent Routing
- [ ] Orchestrator logs routing decision
- [ ] Shows reasoning for next agent selection
- [ ] Frontend displays next agent name
- [ ] Can see "ready" status in logs

### Complete Workflow
- [ ] All 4 agents execute successfully
- [ ] Each agent calls its tools
- [ ] Context flows between agents
- [ ] Final proposal generated

## 🐛 Troubleshooting

### Issue: Sales Agent doesn't call tool
**Check**:
- Agent has tool assigned: Run `python update_agents.py`
- Tool exists in database
- System prompt says "MUST call the extract_sales_objectives tool"

**Fix**:
```powershell
cd agentSystem
python setup_agents.py  # Recreate everything
```

### Issue: Technical Agent tool call fails
**Symptoms**:
```
[DEBUG] Tool result: {"error": "..."}
```

**Check**:
- Flask API running: `curl http://localhost:8080/api/health`
- No firewall blocking port 8080
- CSV files exist in BackendCodes/

**Fix**:
```powershell
cd BackendCodes
python sku_matching_api.py  # Restart Flask
```

### Issue: Intelligent routing doesn't work
**Symptoms**:
- No routing decision in logs
- Error in orchestrator

**Fallback**:
The system automatically falls back to sequential routing if LLM routing fails. Check:
- OpenAI API key is set
- GPT-4 model is accessible
- No rate limiting

### Issue: Context not flowing between agents
**Check**:
- Sales agent returns `extracted_requirements` field
- Technical agent receives context parameter
- Workflow endpoint passes context correctly

**Test manually**:
```python
from services.orchestrator import AgentOrchestrator
from database import SessionLocal

db = SessionLocal()
orch = AgentOrchestrator(db)

# Test routing
decision = orch.select_next_agent(
    current_agent="sales_agent",
    current_output={"response": "Sales analysis complete"},
    context={"sales_summary": {...}}
)
print(decision)
```

## 📊 Expected Tool Call Examples

### Sales Agent Tool Call
```json
{
  "tool": "extract_sales_objectives",
  "arguments": {
    "rfp_text": "PROJECT: Commercial Building Paint...(full RFP)"
  },
  "result": {
    "status": "success",
    "objectives": ["High-quality paint solution", "Durable finish"],
    "requirements": ["15000 sq ft exterior", "5000 sq ft interior"],
    "extracted_requirements": [
      "Exterior emulsion for 15000 sq ft outer walls",
      "Interior emulsion for 5000 sq ft bedrooms and living areas",
      "Primer for wall preparation"
    ],
    "scope": "Complete painting solution for commercial building",
    "budget_info": "₹15-20 lakhs",
    "timeline": "60 days completion",
    "extracted_count": 3
  }
}
```

### Technical Agent Tool Call
```json
{
  "tool": "match_sku_from_csv",
  "arguments": {
    "requirements": [
      "Exterior emulsion for 15000 sq ft outer walls",
      "Interior emulsion for 5000 sq ft bedrooms"
    ],
    "top_k": 5,
    "include_pricing": true
  },
  "result": {
    "matches": [
      {
        "requirement": "Exterior emulsion for 15000 sq ft outer walls",
        "top_matches": [
          {
            "sku_code": "SKU001",
            "product_name": "WeatherShield Exterior Emulsion",
            "category": "Emulsion",
            "type": "Exterior",
            "score": 11.5,
            "unit_price": 450.0,
            "pricing_info": {...}
          }
        ]
      }
    ]
  }
}
```

## 🎯 Key Success Metrics

1. **Tool Execution Rate**: 100% (all agents call their tools)
2. **Routing Accuracy**: LLM correctly identifies next agent
3. **Context Preservation**: Data flows through all 4 agents
4. **Error Rate**: < 5% failures (with proper error handling)
5. **End-to-End Success**: Complete workflow from RFP → Proposal

## 📝 Architecture Summary

```
User Upload RFP
    ↓
Sales Agent
    ├→ Calls: extract_sales_objectives(rfp_text)
    ├→ Returns: structured requirements
    └→ Orchestrator decides next: technical_agent
        ↓
Technical Agent
    ├→ Calls: match_sku_from_csv(requirements=[...])
    ├→ Returns: matched SKUs with scores
    └→ Orchestrator decides next: pricing_agent
        ↓
Pricing Agent
    ├→ Calls: calculate_total_cost(items=[...])
    ├→ Returns: pricing table with totals
    └→ Orchestrator decides next: proposal_assembly_agent
        ↓
Proposal Agent
    ├→ Calls: format_proposal_html(sections={...})
    ├→ Returns: final proposal document
    └→ Workflow Complete
```

## 🔧 Configuration Files Modified

1. **setup_agents.py**: 
   - Fixed `extract_sales_objectives` tool with real implementation
   - Updated all agent system prompts with CRITICAL workflows
   - Fixed UUID serialization issue

2. **orchestrator.py**:
   - Added `select_next_agent()` for intelligent routing
   - Enhanced `execute_agent()` with debug logging
   - Added error handling with traceback

3. **workflow.py**:
   - Integrated intelligent routing
   - Enhanced error messages
   - Added workflow state logging

4. **update_agents.py**:
   - Quick script to update without full setup
   - Assigns tools to agents
   - Updates system prompts

## ✨ Next Steps

1. Monitor tool execution in production
2. Tune agent system prompts based on output quality
3. Add more sophisticated SKU matching logic
4. Implement caching for frequently matched products
5. Add analytics dashboard for workflow metrics
6. Consider adding tool call validation
7. Implement retry logic for failed tool calls
