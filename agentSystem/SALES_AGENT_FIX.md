# Fix for Sales Agent HTTP 500 Error

## Problem Identified

The Sales Agent was failing with HTTP 500 error because:
1. It was configured with a tool `extract_sales_objectives` that was just a placeholder
2. The tool didn't perform any real extraction - just returned a note
3. This caused the agent execution to fail

## Solution Implemented

### 1. Updated Sales Agent
- **Removed the tool requirement** - Sales Agent doesn't need a tool to extract requirements
- Updated system prompt to explicitly instruct the agent to analyze RFP directly
- Added `extracted_requirements` field to ensure clean requirements list for Technical Agent

### 2. Updated Technical Agent  
- Enhanced system prompt with **CRITICAL** instruction to call `match_sku_from_csv` tool
- Added explicit examples of how to format requirements
- Specified that it MUST call the tool before responding

### 3. Added Debug Logging
- Added comprehensive logging in `orchestrator.py` to track:
  - Which agent is executing
  - How many tools it has
  - Tool calls being made
  - Tool results
  - Errors with full stack traces
- Added logging in `workflow.py` to track workflow execution

### 4. Improved Error Handling
- Wrapped agent execution in try-catch with detailed error messages
- Added proper exception propagation
- Removed dead code in workflow.py

## Files Modified

1. **agentSystem/setup_agents.py**
   - Sales Agent: tool_names changed from `["extract_sales_objectives"]` to `[]`
   - Sales Agent: Updated system prompt with explicit instructions
   - Technical Agent: Updated system prompt with CRITICAL instructions to call tool

2. **agentSystem/services/orchestrator.py**
   - Added debug logging throughout `execute_agent()`
   - Added try-catch with traceback printing
   - Tracks tool execution flow

3. **agentSystem/routers/workflow.py**
   - Added logging for workflow steps
   - Improved error handling
   - Removed dead code after exception handler
   - Better message formatting for Technical Agent

4. **agentSystem/update_agents.py** (NEW)
   - Quick script to update agents in database without full setup

## How to Fix and Test

### Step 1: Update Agents in Database
Run the update script to modify the agents:

```powershell
cd agentSystem
python update_agents.py
```

This will:
- Remove tools from Sales Agent
- Update both Sales and Technical Agent system prompts

### Step 2: Start the FastAPI Server
```powershell
cd agentSystem
uvicorn app:app --reload
```

Watch for debug output in the terminal - you'll see:
- `[DEBUG] Executing agent: sales_agent`
- `[DEBUG] Agent has 0 tools: []`
- `[WORKFLOW] Executing step 0 for RFP X`

### Step 3: Start the Flask SKU API (if not running)
In a new terminal:
```powershell
cd BackendCodes
python sku_matching_api.py
```

Should show: `SKU Matching API running on http://localhost:8080`

### Step 4: Test the Workflow

#### Upload an RFP (if needed):
1. Go to your React app at http://localhost:3000
2. Use the "Upload New RFP" button
3. Upload `sample-rfp-commercial-building.txt`

#### Execute Step-by-Step:
1. Select the RFP
2. Click "Start Sales Agent"
3. Watch terminal for debug output:
   ```
   [WORKFLOW] Executing step 0 for RFP 1
   [WORKFLOW] Agent to execute: sales_agent
   [DEBUG] Executing agent: sales_agent
   [DEBUG] Agent has 0 tools: []
   [DEBUG] Calling OpenAI with 2 messages and 0 tools
   [DEBUG] No tool calls made, using direct response
   [DEBUG] Agent execution completed successfully
   ```

4. Approve and continue to Technical Agent
5. Watch for tool call:
   ```
   [DEBUG] Executing agent: technical_agent
   [DEBUG] Agent has 2 tools: ['match_sku_from_csv', 'validate_sku']
   [DEBUG] Agent made 1 tool calls
   [DEBUG] Executing tool: match_sku_from_csv with args: {...}
   [DEBUG] Tool result: {...}
   ```

## Expected Behavior

### Sales Agent (Step 0)
- ✅ No tool calls
- ✅ Returns structured JSON with objectives, requirements, scope
- ✅ Includes `extracted_requirements` list like:
  ```json
  {
    "extracted_requirements": [
      "Exterior emulsion for 15000 sq ft outer walls",
      "Interior emulsion for 5000 sq ft bedrooms",
      "Primer for walls"
    ]
  }
  ```

### Technical Agent (Step 1)
- ✅ Makes tool call to `match_sku_from_csv`
- ✅ Passes requirements array from Sales Agent output
- ✅ Receives matched SKUs with scores and pricing
- ✅ Returns structured response with matched products

### Pricing Agent (Step 2)
- ✅ Takes matched SKUs from Technical Agent
- ✅ Generates pricing table
- ✅ Calculates totals with tax and discounts

### Proposal Agent (Step 3)
- ✅ Compiles all data into final proposal
- ✅ Formats as professional document

## Common Issues and Solutions

### Issue: Still getting HTTP 500
**Check**: 
- Google API key is set: `echo $env:GOOGLE_API_KEY`
- Database is accessible
- Look at terminal for specific error

### Issue: Technical Agent doesn't call tool
**Solution**: 
- The system prompt now has CRITICAL instructions
- If still not calling, check that tools are properly loaded
- Look for `[DEBUG] Agent has 2 tools` in logs

### Issue: Tool call fails
**Check**:
- Flask API is running on port 8080
- Test manually: `curl http://localhost:8080/api/health`
- Check firewall/antivirus blocking

### Issue: Tool returns error
**Solution**:
- Check Flask terminal for errors
- Verify CSV files exist in BackendCodes/
- Test tool directly via Postman

## Verification Checklist

- [ ] `update_agents.py` executed successfully
- [ ] FastAPI server started with `--reload`
- [ ] Flask SKU API running on 8080
- [ ] React frontend accessible at localhost:3000
- [ ] RFP uploaded successfully
- [ ] Sales Agent executes without tools
- [ ] Technical Agent calls match_sku_from_csv tool
- [ ] Tool returns matched SKUs
- [ ] Full workflow completes all 4 steps

## Debug Commands

Check agent configuration in database:
```python
from database import SessionLocal
from models import Agent
db = SessionLocal()
sales = db.query(Agent).filter(Agent.name == "sales_agent").first()
print(f"Tools: {len(sales.tool_ids or [])}")
print(f"Prompt length: {len(sales.system_prompt)}")
```

Test tool directly:
```python
from services.orchestrator import AgentOrchestrator
from database import SessionLocal
db = SessionLocal()
orch = AgentOrchestrator(db)
result = orch.execute_tool("match_sku_from_csv", {
    "requirements": ["exterior paint for walls"],
    "top_k": 3
})
print(result)
```

## Next Steps After Fix

1. Test complete workflow end-to-end
2. Verify all 4 agents execute successfully
3. Check final proposal generation
4. Test with multiple RFPs
5. Review and tune agent prompts based on output quality
