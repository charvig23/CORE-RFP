# SKU Matching Integration Guide

## Overview
This integration adds SKU matching functionality to the C.O.R.E project using a Flask API that matches product requirements to SKU codes from CSV files. The Technical Agent can use this tool to find matching products for RFP requirements.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   React     │─────▶│  Flask API   │─────▶│  CSV Files  │
│  Frontend   │      │  (Port 8080) │      │  SKU/Price  │
└─────────────┘      └──────────────┘      └─────────────┘
       │                     ▲
       │                     │
       ▼                     │
┌─────────────┐      ┌──────────────┐
│  FastAPI    │─────▶│  Technical   │
│  Backend    │      │    Agent     │
│ (Port 8000) │      │  (GPT-4)     │
└─────────────┘      └──────────────┘
```

## Setup Instructions

### 1. Prepare CSV Files

You need two CSV files:

**sku_master.csv** - Contains product information:
```csv
sku_code,product_name,description,category,type,tags
SKU001,Premium Exterior Emulsion,High quality paint for outer walls,Paint,Emulsion,exterior outer walls premium
SKU002,Interior Wall Primer,Base coat for interior walls,Paint,Primer,interior walls base coat
```

**pricing.csv** - Contains pricing information:
```csv
sku_code,price,gst
SKU001,299.99,18
SKU002,199.99,18
```

Place these files in the `BackendCodes/` directory or update the paths in `sku_matching_api.py`.

### 2. Install Dependencies

```bash
# Navigate to agentSystem folder
cd agentSystem

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure Flask API

Edit `BackendCodes/sku_matching_api.py` and update CSV paths:

```python
SKU_CSV = "path/to/your/sku_master.csv"
PRICING_CSV = "path/to/your/pricing.csv"
```

Or set environment variables:
```bash
export SKU_CSV_PATH="path/to/sku_master.csv"
export PRICING_CSV_PATH="path/to/pricing.csv"
```

### 4. Run the Flask API

```bash
cd BackendCodes
python sku_matching_api.py
```

The API will start on `http://localhost:8080`

### 5. Run the FastAPI Backend

```bash
cd agentSystem
uvicorn app:app --reload --port 8000
```

### 6. Setup Database and Agents

```bash
cd agentSystem
python setup_agents.py
```

This will register the `match_sku_from_csv` tool with the Technical Agent.

### 7. Run the React Frontend

```bash
cd C.O.R.E
npm install
npm start
```

Frontend will start on `http://localhost:3000`

## API Endpoints

### Match SKU
**POST** `/api/match-sku`

Request:
```json
{
  "requirements": [
    "Exterior emulsion for outer walls",
    "Interior primer for living room"
  ],
  "top_k": 3,
  "include_pricing": true
}
```

Response:
```json
{
  "matches": [
    {
      "requirement": "Exterior emulsion for outer walls",
      "matches": [
        {
          "sku": "SKU001",
          "product_name": "Premium Exterior Emulsion",
          "description": "High quality paint for outer walls",
          "score": 0.92,
          "raw_score": 11.04,
          "similarity": 0.85,
          "price": 299.99,
          "gst": 18
        }
      ]
    }
  ]
}
```

### Validate SKU
**POST** `/api/validate-sku`

Request:
```json
{
  "sku_code": "SKU001"
}
```

### Health Check
**GET** `/api/health`

## Using the React Component

Add the SKU Matcher component to your React app:

```javascript
import SkuMatcher from './components/SkuMatcher';

function App() {
  return (
    <div>
      <SkuMatcher />
    </div>
  );
}
```

## Agent Tool Usage

The Technical Agent can now use the tool in conversations:

**User Query:** "Find products for exterior wall painting"

**Agent Response:** The agent will automatically call `match_sku_from_csv` with:
```json
{
  "requirements": ["exterior wall paint", "primer for exterior walls"],
  "top_k": 3,
  "include_pricing": true
}
```

## Deployment to Render

### 1. Create Flask App for Render

Create `BackendCodes/requirements_flask.txt`:
```
flask
flask-cors
pandas
```

Create `BackendCodes/render.yaml`:
```yaml
services:
  - type: web
    name: sku-matching-api
    env: python
    buildCommand: pip install -r requirements_flask.txt
    startCommand: python sku_matching_api.py
    envVars:
      - key: PORT
        value: 8080
      - key: SKU_CSV_PATH
        value: /opt/render/project/src/sku_master.csv
      - key: PRICING_CSV_PATH
        value: /opt/render/project/src/pricing.csv
```

### 2. Deploy to Render

1. Push your code to GitHub
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Select the `BackendCodes` folder
5. Upload your CSV files
6. Deploy

### 3. Update URLs

After deployment, update `agentSystem/setup_agents.py`:

```python
"code": "https://your-app.onrender.com/api/match-sku",
```

Run `python setup_agents.py` again to update the tool.

## Testing

### Test Flask API
```bash
curl -X POST http://localhost:8080/api/match-sku \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": ["exterior paint"],
    "top_k": 3
  }'
```

### Test Through Agent
Use the React frontend's Master Agent Chat to ask:
```
"I need to find suitable products for painting the exterior walls of a building"
```

The Technical Agent will use the tool automatically.

## Scoring Algorithm

The matching algorithm uses:
1. **Category matching** (interior/exterior) - 3 points
2. **Type matching** (primer, emulsion, etc.) - 4 points
3. **Token overlap** - up to 3 points
4. **Fuzzy string similarity** - up to 2 points

Maximum score: 12 points (normalized to 0-1)

## Troubleshooting

### API not connecting
- Check if Flask is running on port 8080
- Verify CORS is enabled
- Check firewall settings

### No matches found
- Verify CSV files are loaded correctly
- Check CSV column names match expected format
- Test with simpler requirements

### Agent not using tool
- Verify tool is registered in database
- Check agent has tool assigned in `setup_agents.py`
- Review agent system prompt

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SKU_CSV_PATH` | Path to SKU master CSV | `sku_master.csv` |
| `PRICING_CSV_PATH` | Path to pricing CSV | `pricing.csv` |
| `PORT` | Flask API port | `8080` |

## File Structure

```
R2/
├── BackendCodes/
│   ├── sku_matching_api.py      # Flask API
│   ├── requirements_flask.txt    # Flask dependencies
│   ├── sku_master.csv           # SKU data
│   └── pricing.csv              # Pricing data
├── agentSystem/
│   ├── setup_agents.py          # Tool registration
│   └── requirements.txt         # Updated dependencies
└── C.O.R.E/
    └── src/
        ├── components/
        │   ├── SkuMatcher.jsx   # React component
        │   └── SkuMatcher.css   # Styles
        └── services/
            └── api.js           # Updated API calls
```

## Next Steps

1. ✅ Create sample CSV files with your product data
2. ✅ Test the Flask API locally
3. ✅ Integrate with React frontend
4. ✅ Test agent tool usage
5. 🔲 Deploy to Render
6. 🔲 Update production URLs
7. 🔲 Add authentication if needed
