# SKU Matching System - Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │         React Frontend (localhost:3000)                      │   │
│  │                                                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│  │  │ RFP Inbox   │  │ Master      │  │ SKU Matcher │         │   │
│  │  │             │  │ Agent Chat  │  │ Component   │ ◄─NEW   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │   │
│  │         │                 │                 │                │   │
│  └─────────┼─────────────────┼─────────────────┼────────────────┘   │
│            │                 │                 │                     │
└────────────┼─────────────────┼─────────────────┼─────────────────────┘
             │                 │                 │
             ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       API LAYER                                      │
│                                                                       │
│  ┌──────────────────────────┐    ┌─────────────────────────────┐   │
│  │  FastAPI Backend         │    │  Flask API (SKU Service)    │   │
│  │  (localhost:8000)        │    │  (localhost:8080) ◄─NEW     │   │
│  │                          │    │                              │   │
│  │  ┌────────────────────┐  │    │  ┌────────────────────────┐ │   │
│  │  │ /rfp/list          │  │    │  │ /api/match-sku         │ │   │
│  │  │ /rfp/analyze       │  │    │  │ /api/validate-sku      │ │   │
│  │  │ /agent/execute     │  │    │  │ /api/health            │ │   │
│  │  └────────────────────┘  │    │  └────────────────────────┘ │   │
│  │                          │    │                              │   │
│  └────────────┬─────────────┘    └──────────────┬───────────────┘   │
│               │                                  │                   │
└───────────────┼──────────────────────────────────┼───────────────────┘
                │                                  │
                ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       AGENT LAYER                                    │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Agent Orchestrator                               │   │
│  │                                                               │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐  │   │
│  │  │  Sales    │  │ Technical │  │  Pricing  │  │ Proposal │  │   │
│  │  │  Agent    │  │  Agent    │  │  Agent    │  │ Assembly │  │   │
│  │  │           │  │           │  │           │  │  Agent   │  │   │
│  │  │  GPT-4    │  │  GPT-4    │  │  GPT-4    │  │  GPT-4   │  │   │
│  │  └───────────┘  └─────┬─────┘  └───────────┘  └──────────┘  │   │
│  │                       │                                       │   │
│  │                       │ Uses Tool                             │   │
│  │                       ▼                                       │   │
│  │              ┌─────────────────┐                              │   │
│  │              │ match_sku_from_ │ ◄─NEW TOOL                   │   │
│  │              │      csv        │                              │   │
│  │              └─────────────────┘                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                     │
│                                                                       │
│  ┌─────────────────┐    ┌──────────────────────────────────────┐   │
│  │   PostgreSQL    │    │    CSV Files ◄─NEW                    │   │
│  │   Database      │    │                                        │   │
│  │                 │    │  ┌──────────────┐  ┌───────────────┐  │   │
│  │  - Agents       │    │  │ sku_master   │  │ pricing.csv   │  │   │
│  │  - Tools        │    │  │  .csv        │  │               │  │   │
│  │  - RFPs         │    │  │              │  │  - SKU codes  │  │   │
│  │  - Conversations│    │  │  - Products  │  │  - Prices     │  │   │
│  │                 │    │  │  - Desc.     │  │  - GST rates  │  │   │
│  └─────────────────┘    │  │  - Category  │  │               │  │   │
│                         │  │  - Type      │  │               │  │   │
│                         │  └──────────────┘  └───────────────┘  │   │
│                         └──────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow: SKU Matching Request

```
┌──────────┐
│   User   │
│  enters  │
│  "Find   │
│ exterior │
│  paint"  │
└────┬─────┘
     │
     ▼
┌─────────────────┐
│ Option A:       │
│ Direct UI       │
│ (SkuMatcher)    │
└────┬────────────┘
     │
     │ POST /api/match-sku
     │ { requirements: ["exterior paint"] }
     │
     ▼
┌────────────────────────┐
│  Flask API             │
│  1. Normalize text     │
│  2. Score each SKU     │
│  3. Rank results       │
│  4. Attach pricing     │
└────┬───────────────────┘
     │
     │ Response
     │ { matches: [...] }
     │
     ▼
┌─────────────────┐
│  React UI       │
│  Display cards  │
│  with scores &  │
│  pricing        │
└─────────────────┘


┌──────────┐
│   User   │
│ asks via │
│  Agent   │
│  Chat    │
└────┬─────┘
     │
     ▼
┌─────────────────┐
│ Option B:       │
│ Master Agent    │
│ Chat            │
└────┬────────────┘
     │
     │ POST /agent/execute
     │ { message: "Find exterior paint" }
     │
     ▼
┌────────────────────────┐
│  Technical Agent       │
│  (GPT-4)               │
│  1. Parse request      │
│  2. Decide to use tool │
│  3. Call tool          │
└────┬───────────────────┘
     │
     │ Tool call: match_sku_from_csv
     │ { requirements: ["exterior paint"] }
     │
     ▼
┌────────────────────────┐
│  Tool Runtime          │
│  Proxy to Flask API    │
└────┬───────────────────┘
     │
     │ HTTP POST
     │
     ▼
┌────────────────────────┐
│  Flask API             │
│  Process & Return      │
└────┬───────────────────┘
     │
     │ Results
     │
     ▼
┌────────────────────────┐
│  Technical Agent       │
│  Format response       │
└────┬───────────────────┘
     │
     │ Agent response
     │
     ▼
┌─────────────────┐
│  User sees      │
│  matched SKUs   │
│  with details   │
└─────────────────┘
```

## Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                    SkuMatcher Component                      │
│                                                               │
│  State:                                                       │
│  - requirements: [""]                                         │
│  - loading: false                                             │
│  - results: null                                              │
│  - topK: 3                                                    │
│  - includePricing: true                                       │
│                                                               │
│  Methods:                                                     │
│  - addRequirement()                                           │
│  - removeRequirement(index)                                   │
│  - updateRequirement(index, value)                            │
│  - matchSkus() ────────────────┐                             │
│                                 │                             │
└─────────────────────────────────┼─────────────────────────────┘
                                  │
                                  │ API Call
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   api.js (Service)      │
                    │                         │
                    │  export const matchSku  │
                    │  = (payload) =>         │
                    │    SKU_API.post(        │
                    │      "/api/match-sku",  │
                    │      payload            │
                    │    )                    │
                    └────────┬────────────────┘
                             │
                             │ HTTP POST
                             │
                             ▼
              ┌──────────────────────────────┐
              │    Flask API Handler         │
              │                              │
              │  @app.route("/api/match-sku")│
              │  def match_sku():            │
              │    1. Validate input         │
              │    2. For each requirement:  │
              │       - Score all SKUs       │
              │       - Sort by score        │
              │       - Take top K           │
              │       - Attach pricing       │
              │    3. Return JSON            │
              └──────────────────────────────┘
```

## Scoring Algorithm Flow

```
Input: "Exterior emulsion for outer walls"
                │
                ▼
        ┌───────────────┐
        │  Normalize    │
        │  Text         │
        └───────┬───────┘
                │
                ▼
        "exterior emulsion outer walls"
                │
                ▼
        ┌───────────────────────┐
        │  Tokenize             │
        │  {exterior, emulsion, │
        │   outer, walls}       │
        └───────┬───────────────┘
                │
                ▼
    ┌───────────────────────────────┐
    │   For Each SKU in Database    │
    └───────────┬───────────────────┘
                │
                ▼
    ┌────────────────────────────────┐
    │   Score Components:            │
    │                                │
    │   1. Category Match            │
    │      "exterior" in both? +3pts │
    │                                │
    │   2. Type Match                │
    │      "emulsion" in both? +4pts │
    │                                │
    │   3. Token Overlap             │
    │      Common tokens? +0-3pts    │
    │                                │
    │   4. Fuzzy Similarity          │
    │      Overall match? +0-2pts    │
    │                                │
    │   Total: 0-12 points           │
    │   Normalized: 0.0-1.0          │
    └────────────┬───────────────────┘
                 │
                 ▼
    ┌────────────────────────────────┐
    │   Sort by Score (descending)   │
    │                                │
    │   1. SKU001 - Score: 0.92      │
    │   2. SKU007 - Score: 0.78      │
    │   3. SKU003 - Score: 0.65      │
    │   ...                          │
    └────────────┬───────────────────┘
                 │
                 ▼
    ┌────────────────────────────────┐
    │   Take Top K (default: 3)      │
    │   Attach Pricing Data          │
    │   Return JSON                  │
    └────────────────────────────────┘
```

## File Dependencies

```
sku_matching_api.py
    │
    ├── Imports
    │   ├── flask (Flask, request, jsonify)
    │   ├── flask_cors (CORS)
    │   ├── pandas (read CSV)
    │   ├── re (text normalization)
    │   └── difflib (fuzzy matching)
    │
    ├── Loads CSV Files
    │   ├── sku_master.csv
    │   └── pricing.csv
    │
    └── Endpoints
        ├── POST /api/match-sku
        ├── POST /api/validate-sku
        └── GET /api/health

SkuMatcher.jsx
    │
    ├── Imports
    │   ├── React (useState)
    │   └── ./SkuMatcher.css
    │
    ├── Uses API
    │   └── fetch("http://localhost:8080/api/match-sku")
    │
    └── Renders UI
        ├── Requirement inputs
        ├── Options (top_k, pricing)
        ├── Match button
        └── Results display

setup_agents.py
    │
    ├── Defines Tools
    │   └── match_sku_from_csv
    │       ├── name
    │       ├── description
    │       ├── tool_type: "api"
    │       ├── code: "http://localhost:8080/api/match-sku"
    │       └── parameters (JSON schema)
    │
    └── Assigns to Agents
        └── Technical Agent
            └── tool_ids: [match_sku_tool.id]
```

## Deployment Architecture

```
Development (localhost)
┌──────────────────────────────────────┐
│  React:  localhost:3000              │
│  Flask:  localhost:8080              │
│  FastAPI: localhost:8000             │
│  DB:     localhost:5432              │
└──────────────────────────────────────┘

Production (Render/Cloud)
┌──────────────────────────────────────┐
│  React:  your-app.vercel.app         │
│  Flask:  sku-api.onrender.com        │
│  FastAPI: backend.onrender.com       │
│  DB:     managed-postgres.cloud      │
└──────────────────────────────────────┘
```

This architecture provides a clean separation of concerns with the Flask API handling SKU matching logic independently, while being accessible both directly from the UI and through the agent system.
