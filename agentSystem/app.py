from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import agents as agents_router
from routers import workflow as workflow_router

# These imports must be explicit so Base registers the models
from models import Agent, Tool, RFP, AgentExecution, Conversation

# Create all tables in database on startup
Base.metadata.create_all(bind=engine)
print("✓ Tables created successfully")

app = FastAPI(title="CORE-RFP Agent System")

# Allow React frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_router.router)
app.include_router(workflow_router.router)

@app.get("/")
def root():
    return {"message": "CORE-RFP Agent System is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}