from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import agents, tools, rfp, workflow
from database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agent System with DB")

# Add CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (use specific origins in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    """Root endpoint - API welcome message"""
    return {
        "message": "Multi-Agent RFP Processing System",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "agents": "/agents",
            "tools": "/tools",
            "rfp": "/rfp",
            "workflow": "/workflow"
        }
    }

app.include_router(agents.router)
app.include_router(tools.router)
app.include_router(rfp.router)
app.include_router(workflow.router)
