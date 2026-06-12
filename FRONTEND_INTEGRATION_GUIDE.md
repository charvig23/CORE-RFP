# 🎯 C.O.R.E Frontend Integration Guide

## Complete Setup: Backend + Frontend Integration

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    C.O.R.E Frontend                      │
│                   (React - Port 3000)                    │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴──────────────┐
        │                           │
┌───────▼──────────┐     ┌─────────▼──────────┐
│  agentSystem     │     │   BackendCodes     │
│  (FastAPI)       │────▶│   (Flask)          │
│  Port 8000       │     │   Port 8080        │
│                  │     │                    │
│ - RFP Management │     │ - Tool Execution   │
│ - Agent Pipeline │     │ - SKU Matching     │
│ - Orchestration  │     │ - PDF Generation   │
│ - HITL Workflow  │     │ - Validation       │
└──────────────────┘     └────────────────────┘
         │
         ▼
┌──────────────────┐
│   PostgreSQL     │
│   Database       │
└──────────────────┘
```

---

## 🚀 Quick Start

### Step 1: Start Backend Services

#### Terminal 1: Flask Tool API (Port 8080)
```powershell
cd 'C:\Users\CHARVI\OneDrive\Desktop\COLLEGE\EY TECHATHON 6.0\R2\BackendCodes'
python sku_matching_api.py
```

**Expected Output:**
```
 * Running on http://localhost:8080
```

#### Terminal 2: FastAPI Agent System (Port 8000)
```powershell
cd 'C:\Users\CHARVI\OneDrive\Desktop\COLLEGE\EY TECHATHON 6.0\R2\agentSystem'
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Start Frontend

#### Terminal 3: React Frontend (Port 3000)
```powershell
cd 'C:\Users\CHARVI\OneDrive\Desktop\COLLEGE\EY TECHATHON 6.0\R2\C.O.R.E'
npm install
npm start
```

**Expected Output:**
```
Compiled successfully!
Local: http://localhost:3000
```

---

## 📋 Complete Workflow

### 1. Upload RFP
- Navigate to http://localhost:3000
- Click "Upload New RFP"
- Select PDF or TXT file
- File is uploaded and text extracted

### 2. Automatic Agent Pipeline
When you select an RFP, agents execute sequentially:

```
Sales Agent (💼)
    ↓ Extracts: Requirements, objectives, budget
Technical Agent (🔧)
    ↓ Matches: SKUs, validates products
Pricing Agent (💰)
    ↓ Generates: Pricing table, totals
Proposal Agent (📄)
    ↓ Creates: Proposal draft (PAUSES HERE)
```

### 3. Human Review (HITL)
- **RFP Summary displayed** after pricing completion
  - Sales insights
  - Technical solution
  - Pricing summary
  
- **Proposal Draft** shown for editing
  - Executive Summary
  - Understanding of Requirements
  - Proposed Solution
  - Pricing Details
  - Payment Terms
  - Implementation Timeline
  - Terms and Conditions

### 4. Approve & Generate PDF
- Edit sections as needed
- Click "Approve & Generate PDF"
- System calls Flask API to create PDF
- Download link provided

---

## 🔧 API Endpoints Used

### FastAPI (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rfp/list` | GET | List all RFPs |
| `/rfp/upload-file` | POST | Upload RFP PDF/TXT |
| `/rfp/{id}/analyze` | POST | Run full agent pipeline |
| `/rfp/{id}/proposal-draft` | GET | Get editable proposal |
| `/rfp/{id}/approve-proposal` | POST | Approve & generate PDF |

### Flask (Port 8080)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/match-sku` | POST | Match products to requirements |
| `/api/validate-sku` | POST | Validate SKU details |
| `/api/generate-proposal-pdf` | POST | Generate PDF from sections |
| `/proposals/<filename>` | GET | Download PDF file |

---

## 🎨 Frontend Components

### IntegratedWorkflow.jsx
**Main Component** - Complete end-to-end workflow
- RFP upload
- Agent progress visualization
- RFP summary display
- Proposal editor (HITL)
- PDF download

**Features:**
- Sequential agent execution
- Real-time progress indicators
- Editable proposal sections
- Error handling
- Loading states

### AgentWorkflow.jsx
**Step-by-Step Mode** - Manual agent execution
- Execute one agent at a time
- Review output before proceeding
- More control over workflow

---

## 📦 Frontend State Management

```javascript
// Main state structure
{
  selectedRfp: {...},
  workflowState: 'idle' | 'analyzing' | 'awaiting_approval' | 'generating_pdf' | 'complete',
  agentProgress: [
    { name: 'Sales Agent', status: 'completed', icon: '💼' },
    { name: 'Technical Agent', status: 'running', icon: '🔧' },
    // ...
  ],
  rfpSummary: {
    sales_insights: "...",
    technical_solution: "...",
    pricing_summary: "..."
  },
  proposalDraft: {
    title: "Response Proposal",
    sections: { ... },
    metadata: { ... }
  },
  pdfInfo: {
    filename: "proposal_rfp_....pdf",
    download_url: "http://localhost:8080/proposals/...",
    file_size: 5248
  }
}
```

---

## 🔄 Agent Communication Flow

### 1. Frontend → FastAPI
```javascript
// Upload RFP
POST /rfp/upload-file
FormData: { file: <PDF/TXT> }

Response: { rfp_id: 1, filename: "...", text_length: 1500 }
```

### 2. Start Workflow
```javascript
// Trigger full pipeline
POST /rfp/1/analyze

// FastAPI Orchestrator executes:
// 1. Sales Agent
// 2. Technical Agent
//    ├─ Calls Flask: POST /api/match-sku
//    └─ Calls Flask: POST /api/validate-sku (multiple)
// 3. Pricing Agent
//    ├─ Calls Flask: POST /api/calculate-cost
//    └─ Calls Flask: POST /api/generate-pricing-table
// 4. Proposal Agent (generates draft, NO PDF yet)

Response: {
  rfp_summary: { ... },
  proposal_draft: { sections: {...} },
  requires_approval: true
}
```

### 3. Human Approves
```javascript
// Frontend sends edited proposal
POST /rfp/1/approve-proposal
Body: {
  title: "...",
  sections: { ... },
  approved: true
}

// FastAPI calls Flask: POST /api/generate-proposal-pdf
// Flask generates PDF with ReportLab

Response: {
  status: "Proposal approved and PDF generated",
  pdf_info: {
    filename: "...",
    download_url: "http://localhost:8080/proposals/...",
    file_size: 5248
  }
}
```

---

## 🎯 Key Features Implemented

✅ **Sequential Agent Execution**
- Sales → Technical → Pricing → Proposal
- Each agent receives previous agent's output
- Context flows through the pipeline

✅ **RFP Summary Display**
- Shows after pricing agent completes
- Consolidates sales, technical, and pricing insights
- Displayed before proposal generation

✅ **Human-in-the-Loop (HITL)**
- Proposal draft generated first
- Human can review and edit all sections
- PDF only generated after approval

✅ **Real-time Progress Tracking**
- Visual agent pipeline
- Status indicators (pending/running/completed)
- Animated states

✅ **Error Handling**
- Network errors caught
- User-friendly error messages
- Workflow can be reset

---

## 🧪 Testing the Integration

### Test Scenario 1: Simple RFP
1. Upload: `sample_rfp.txt` (text file with product requirements)
2. Observe: All 4 agents execute automatically
3. Verify: RFP summary appears after pricing
4. Edit: Modify pricing section
5. Approve: Generate PDF
6. Download: Click download link

### Test Scenario 2: PDF Upload
1. Upload: `rfp_document.pdf`
2. Check: Text extraction works
3. Process: Full pipeline
4. Review: Editable draft
5. Approve: Generate final PDF

### Test Scenario 3: Manual Mode
1. Switch to "Step-by-Step Mode" tab
2. Select RFP
3. Execute each agent manually
4. Review outputs between steps

---

## 🐛 Troubleshooting

### Issue: CORS Error
**Symptom:** Network request blocked in browser console

**Fix:** Ensure FastAPI has CORS middleware (should be in `app.py`)
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Port Already in Use
**Symptom:** `OSError: [Errno 48] Address already in use`

**Fix:**
```powershell
# Find process on port
netstat -ano | findstr :8000
# Kill process
taskkill /PID <PID> /F
```

### Issue: Agent Not Calling Tools
**Symptom:** Technical agent doesn't call validate_sku

**Fix:** Update agent via Postman (see previous instructions)

### Issue: PDF Generation Fails
**Symptom:** Approval succeeds but no PDF

**Fix:** Check Flask server logs for ReportLab errors
```powershell
# Reinstall ReportLab
pip install --upgrade reportlab
```

---

## 📊 Monitoring

### Backend Logs
- FastAPI: Watch terminal 2 for agent execution
- Flask: Watch terminal 1 for tool calls
- Database: Check PostgreSQL logs

### Frontend Console
- Open browser DevTools (F12)
- Network tab: See API calls
- Console: Check for errors

---

## 🎉 Success Criteria

Your integration is working correctly if:

✅ You can upload an RFP from the frontend
✅ All 4 agents execute automatically in sequence
✅ RFP summary displays after pricing
✅ Proposal draft is editable
✅ PDF generates after approval
✅ Download link works

---

## 📝 Next Steps

1. **Enhance UI:** Add more visualizations, charts
2. **Real-time Updates:** WebSocket for live agent execution
3. **History:** View past RFP processing history
4. **Comparison:** Compare multiple proposals
5. **Templates:** Save proposal templates
6. **Export:** Export to Word, Excel formats

---

## 🔗 URLs

- **Frontend:** http://localhost:3000
- **FastAPI Docs:** http://localhost:8000/docs
- **Flask Health:** http://localhost:8080/api/health
- **PostgreSQL:** localhost:5432

---

## 📧 Support

For issues or questions, check:
1. Terminal logs for error messages
2. Browser console for frontend errors
3. API documentation at `/docs` endpoints

Happy integrating! 🚀
