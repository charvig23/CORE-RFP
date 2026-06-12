# SKU Matching Integration - Quick Reference

## 🎯 What Was Implemented

A complete SKU matching system that allows the Technical Agent to match product requirements with SKU codes from CSV files using intelligent fuzzy matching and scoring.

### Components Created:

1. **Flask API** (`BackendCodes/sku_matching_api.py`)
   - Match SKUs based on requirements
   - Validate SKU existence
   - Include pricing information
   - Health check endpoint

2. **React Component** (`C.O.R.E/src/components/SkuMatcher.jsx`)
   - User-friendly UI for SKU matching
   - Multiple requirement inputs
   - Real-time results display
   - Pricing information visualization

3. **Agent Tool Integration** (Updated `agentSystem/setup_agents.py`)
   - Registered `match_sku_from_csv` tool
   - Updated `validate_sku` tool
   - Connected to Flask API endpoints

4. **Sample Data** (CSV files)
   - `sku_master.csv` - 10 sample SKUs with descriptions
   - `pricing.csv` - Corresponding pricing data

## 🚀 Quick Start

### Option 1: Using PowerShell Script
```powershell
.\start_sku_system.ps1
```

### Option 2: Manual Start

**Terminal 1 - Flask API:**
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

## 🧪 Testing

### Test the Flask API:
```bash
cd BackendCodes
python test_sku_api.py
```

### Test via curl:
```bash
curl -X POST http://localhost:8080/api/match-sku ^
  -H "Content-Type: application/json" ^
  -d "{\"requirements\": [\"exterior paint\"], \"top_k\": 3}"
```

### Test through React UI:
1. Navigate to `http://localhost:3000`
2. Find and open the SKU Matcher component
3. Enter requirements like "Exterior wall paint"
4. Click "Match SKUs"

## 📁 File Structure

```
R2/
├── BackendCodes/
│   ├── sku_matching_api.py          # Main Flask API
│   ├── sku_master.csv               # SKU database
│   ├── pricing.csv                  # Pricing data
│   ├── requirements_flask.txt       # Flask dependencies
│   └── test_sku_api.py              # Test suite
├── agentSystem/
│   ├── setup_agents.py              # Updated with new tool
│   └── requirements.txt             # Updated dependencies
├── C.O.R.E/
│   └── src/
│       ├── components/
│       │   ├── SkuMatcher.jsx       # React UI component
│       │   └── SkuMatcher.css       # Styles
│       └── services/
│           └── api.js               # Updated API functions
├── SKU_MATCHING_GUIDE.md            # Detailed documentation
├── start_sku_system.ps1             # Quick start script
└── SKU_INTEGRATION_README.md        # This file
```

## 🔧 Configuration

### Environment Variables

```bash
# Flask API Configuration
export SKU_CSV_PATH="path/to/sku_master.csv"
export PRICING_CSV_PATH="path/to/pricing.csv"
export PORT=8080

# Or set in Windows
$env:SKU_CSV_PATH="path\to\sku_master.csv"
$env:PRICING_CSV_PATH="path\to\pricing.csv"
$env:PORT=8080
```

### Update Deployed URL

When deploying to Render or another service, update in `agentSystem/setup_agents.py`:

```python
"code": "https://your-app.onrender.com/api/match-sku",
```

Then re-run:
```bash
cd agentSystem
python setup_agents.py
```

## 📊 API Endpoints

### 1. Match SKU
```
POST /api/match-sku
Content-Type: application/json

Body:
{
  "requirements": ["exterior paint", "wood varnish"],
  "top_k": 3,
  "include_pricing": true
}
```

### 2. Validate SKU
```
POST /api/validate-sku
Content-Type: application/json

Body:
{
  "sku_code": "SKU001"
}
```

### 3. Health Check
```
GET /api/health
```

## 🤖 Using with Agents

The Technical Agent can now automatically use this tool. Example queries:

- "Find products for exterior wall painting"
- "I need a primer for interior rooms"
- "Match these requirements: exterior emulsion, wood varnish, metal paint"

The agent will:
1. Parse the requirements
2. Call `match_sku_from_csv` tool
3. Receive ranked matches with scores
4. Present results to user

## 🎨 Scoring Algorithm

The matching uses a weighted scoring system:

| Criterion | Weight | Example |
|-----------|--------|---------|
| Category Match | 3 points | "exterior" matches "exterior" |
| Type Match | 4 points | "emulsion" matches "emulsion" |
| Token Overlap | up to 3 | Common words between requirement and product |
| Fuzzy Similarity | up to 2 | Overall text similarity |

**Maximum Score:** 12 points (normalized to 0-1 scale)

## 📦 Dependencies

### Python (Flask API)
- flask==3.0.0
- flask-cors==4.0.0
- pandas==2.1.4

### Python (FastAPI Backend)
- All existing dependencies plus:
- flask
- flask-cors
- pandas

### React Frontend
- axios (already present)

## 🔐 Security Notes

For production deployment:
1. Add authentication to API endpoints
2. Implement rate limiting
3. Validate and sanitize all inputs
4. Use HTTPS
5. Protect CSV files or use database

## 📈 Future Enhancements

Possible improvements:
- [ ] Database storage instead of CSV
- [ ] Caching for faster lookups
- [ ] Bulk import functionality
- [ ] Advanced filtering options
- [ ] Export matched results
- [ ] Integration with inventory systems
- [ ] Machine learning for better matching

## 🐛 Troubleshooting

### Flask API won't start
- Check if port 8080 is available: `netstat -ano | findstr :8080`
- Verify CSV files exist in correct location
- Check Python version (3.8+ required)

### No matches returned
- Verify CSV data is loaded (check health endpoint)
- Try simpler requirements
- Check CSV format matches expected columns

### Agent not using tool
- Ensure FastAPI backend is running
- Run `setup_agents.py` to register tool
- Check agent system prompts include tool usage instructions

### CORS errors in browser
- Verify Flask CORS is enabled
- Check API URL in frontend matches Flask port
- Clear browser cache

## 📞 Support

For detailed documentation, see: `SKU_MATCHING_GUIDE.md`

For API testing: Run `python BackendCodes/test_sku_api.py`

## ✅ Checklist

- [x] Flask API created
- [x] Sample CSV files added
- [x] Agent tool registered
- [x] React component created
- [x] API service updated
- [x] Test suite created
- [x] Documentation written
- [ ] Local testing completed
- [ ] Deployed to production
- [ ] Production URLs updated

---

**Ready to go!** Start all three services and begin matching SKUs. 🎉
