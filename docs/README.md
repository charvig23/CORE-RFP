# 📚 SKU Matching Integration - Complete Documentation Index

## 🎯 Quick Links

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** | Overview of everything created | 5 min |
| **[SKU_INTEGRATION_README.md](SKU_INTEGRATION_README.md)** | Quick reference guide | 3 min |
| **[SKU_MATCHING_GUIDE.md](SKU_MATCHING_GUIDE.md)** | Comprehensive setup & deployment | 15 min |
| **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** | Visual system architecture | 5 min |

---

## 🚀 Getting Started (Choose Your Path)

### Path 1: Quick Start (Recommended)
1. Run `install_dependencies.bat` to install all packages
2. Start services manually in 3 terminals (see below)
3. Test with `python BackendCodes/test_sku_api.py`

### Path 2: Automated Start
1. Run `.\start_sku_system.ps1` (PowerShell)
2. Follow on-screen instructions

### Path 3: Read First, Then Start
1. Read **IMPLEMENTATION_SUMMARY.md** for overview
2. Read **SKU_MATCHING_GUIDE.md** for details
3. Follow setup instructions there

---

## 📁 File Reference

### Core Implementation Files

| File | Location | Purpose |
|------|----------|---------|
| **sku_matching_api.py** | `BackendCodes/` | Flask API - main matching service |
| **SkuMatcher.jsx** | `C.O.R.E/src/components/` | React UI component |
| **SkuMatcher.css** | `C.O.R.E/src/components/` | Component styles |
| **api.js** | `C.O.R.E/src/services/` | API service functions |
| **setup_agents.py** | `agentSystem/` | Agent & tool registration |

### Data Files

| File | Location | Purpose |
|------|----------|---------|
| **sku_master.csv** | `BackendCodes/` | Product database (10 samples) |
| **pricing.csv** | `BackendCodes/` | Pricing data |

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| **requirements.txt** | `agentSystem/` | FastAPI dependencies |
| **requirements_flask.txt** | `BackendCodes/` | Flask dependencies |
| **package.json** | `C.O.R.E/` | React dependencies |

### Testing & Setup Scripts

| File | Location | Purpose |
|------|----------|---------|
| **test_sku_api.py** | `BackendCodes/` | Automated test suite |
| **start_sku_system.ps1** | Root | PowerShell startup script |
| **install_dependencies.bat** | Root | Dependency installer |

### Documentation Files

| File | Location | Purpose |
|------|----------|---------|
| **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** | docs/ | What was built |
| **[SKU_INTEGRATION_README.md](SKU_INTEGRATION_README.md)** | docs/ | Quick reference |
| **[SKU_MATCHING_GUIDE.md](SKU_MATCHING_GUIDE.md)** | docs/ | Detailed guide |
| **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** | docs/ | Visual diagrams |
| **README.md** | docs/ | This file |

---

## 🎯 Common Tasks

### Starting the System

**Terminal 1 - Flask API:**
```bash
cd "C:\Users\CHARVI\OneDrive\Desktop\COLLEGE\EY TECHATHON 6.0\R2\BackendCodes"
python sku_matching_api.py
```

**Terminal 2 - FastAPI:**
```bash
cd "C:\Users\CHARVI\OneDrive\Desktop\COLLEGE\EY TECHATHON 6.0\R2\agentSystem"
uvicorn app:app --reload --port 8000
```

**Terminal 3 - React:**
```bash
cd "C:\Users\CHARVI\OneDrive\Desktop\COLLEGE\EY TECHATHON 6.0\R2\C.O.R.E"
npm start
```

### Testing

**Test Flask API:**
```bash
cd BackendCodes
python test_sku_api.py
```

**Test via curl:**
```bash
curl -X POST http://localhost:8080/api/match-sku ^
  -H "Content-Type: application/json" ^
  -d "{\"requirements\": [\"exterior paint\"], \"top_k\": 3}"
```

**Test via React UI:**
1. Open http://localhost:3000
2. Navigate to SKU Matcher
3. Enter "Exterior emulsion for outer walls"
4. Click "Match SKUs"

### Updating CSV Data

1. Edit `BackendCodes/sku_master.csv` with your products
2. Edit `BackendCodes/pricing.csv` with your prices
3. Restart Flask API
4. Test with health check: `curl http://localhost:8080/api/health`

### Deploying to Production

1. Deploy Flask API to Render (see **SKU_MATCHING_GUIDE.md** § Deployment)
2. Update URL in `agentSystem/setup_agents.py`
3. Run `python setup_agents.py`
4. Update URL in `C.O.R.E/src/services/api.js`
5. Deploy React app
6. Deploy FastAPI backend

---

## 🔍 Searching This Documentation

### Looking for...

**"How do I start everything?"**
→ See **Starting the System** above or **SKU_INTEGRATION_README.md**

**"What was actually created?"**
→ Read **IMPLEMENTATION_SUMMARY.md**

**"How does the scoring work?"**
→ See **SKU_MATCHING_GUIDE.md** § Scoring Algorithm

**"How do I deploy this?"**
→ See **SKU_MATCHING_GUIDE.md** § Deployment to Render

**"What are the API endpoints?"**
→ See **SKU_INTEGRATION_README.md** § API Endpoints

**"How does the system fit together?"**
→ See **ARCHITECTURE_DIAGRAM.md**

**"How do I test it?"**
→ See **Testing** above or **IMPLEMENTATION_SUMMARY.md** § Testing

**"What CSV format do I need?"**
→ See **SKU_MATCHING_GUIDE.md** § Prepare CSV Files

**"How does the agent use this?"**
→ See **IMPLEMENTATION_SUMMARY.md** § Tool Schema

**"Something broke, how do I fix it?"**
→ See **SKU_INTEGRATION_README.md** § Troubleshooting

---

## 📊 System Components Overview

### Backend Services
- **Flask API (Port 8080)** - SKU matching logic
- **FastAPI (Port 8000)** - Agent orchestration
- **PostgreSQL** - Agent/tool/RFP data

### Frontend
- **React (Port 3000)** - User interface
- **SkuMatcher Component** - Direct UI access
- **Master Agent Chat** - Agent-based access

### Data Layer
- **sku_master.csv** - Product catalog
- **pricing.csv** - Pricing information
- **PostgreSQL** - System data

### Agent System
- **Sales Agent** - RFP analysis
- **Technical Agent** - Uses `match_sku_from_csv` tool ✨
- **Pricing Agent** - Cost calculations
- **Proposal Assembly** - Final document

---

## 🎓 Learning Path

### Beginner (Just Getting Started)
1. Read **IMPLEMENTATION_SUMMARY.md** (5 min)
2. Run `install_dependencies.bat`
3. Start all services manually
4. Test with `test_sku_api.py`
5. Try the React UI

### Intermediate (Ready to Customize)
1. Read **SKU_MATCHING_GUIDE.md**
2. Update CSV files with your data
3. Customize scoring in `sku_matching_api.py`
4. Modify React UI styling
5. Test with your data

### Advanced (Production Deployment)
1. Read **SKU_MATCHING_GUIDE.md** § Deployment
2. Set up Render account
3. Deploy Flask API
4. Update all URLs
5. Deploy frontend
6. Configure production database
7. Set up monitoring

---

## 🛠️ Maintenance

### Regular Tasks
- Update CSV files with new products
- Monitor API performance
- Check logs for errors
- Update dependencies periodically

### When Things Change
- **New products?** → Update `sku_master.csv`
- **Price changes?** → Update `pricing.csv`
- **New requirements?** → Adjust scoring in API
- **UI changes?** → Edit `SkuMatcher.jsx`
- **Deployment URL changed?** → Update `setup_agents.py` and `api.js`

---

## 💡 Tips & Best Practices

### Performance
- Use appropriate `top_k` values (3-5 usually sufficient)
- Consider caching for frequently searched terms
- Monitor API response times
- Use database instead of CSV for large datasets

### Data Quality
- Keep product descriptions detailed
- Use consistent category/type naming
- Update pricing regularly
- Add meaningful tags to products

### Development
- Test locally before deploying
- Keep CSV backups
- Use version control
- Document custom changes

### Production
- Use environment variables for configuration
- Implement proper error handling
- Add authentication if needed
- Set up monitoring and logging
- Use HTTPS in production

---

## 📞 Support Resources

### Documentation Files
- **Implementation details:** IMPLEMENTATION_SUMMARY.md
- **Quick reference:** SKU_INTEGRATION_README.md
- **Setup guide:** SKU_MATCHING_GUIDE.md
- **Architecture:** ARCHITECTURE_DIAGRAM.md

### Code Comments
- Flask API has inline documentation
- React component has JSDoc comments
- Agent setup has detailed comments

### Testing
- Automated tests: `test_sku_api.py`
- Manual testing guide in docs
- Sample data provided

---

## ✅ Checklist for Success

### Setup Phase
- [ ] Read IMPLEMENTATION_SUMMARY.md
- [ ] Install dependencies
- [ ] Start all three services
- [ ] Run test suite
- [ ] Test via React UI
- [ ] Test via Agent chat

### Customization Phase
- [ ] Replace sample CSV with real data
- [ ] Test with your data
- [ ] Adjust scoring if needed
- [ ] Customize UI if desired
- [ ] Update documentation

### Deployment Phase
- [ ] Deploy Flask API
- [ ] Update URLs in code
- [ ] Deploy FastAPI
- [ ] Deploy React frontend
- [ ] Configure production database
- [ ] Test production system
- [ ] Set up monitoring

---

## 🎉 You're All Set!

All documentation is ready. Start with **IMPLEMENTATION_SUMMARY.md** for a complete overview, then move to the specific guides as needed.

**Questions?** Check the troubleshooting sections in each guide.

**Ready to start?** Run `install_dependencies.bat` and follow the setup instructions!

---

*Last Updated: December 10, 2025*
*Version: 1.0*
*Project: C.O.R.E SKU Matching Integration*
