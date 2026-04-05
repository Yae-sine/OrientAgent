"""
OrientAgent - FastAPI Main Application

Entry point for the OrientAgent API server.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.routers import session
from api.schemas import HealthResponse

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Initializes ChromaDB and LangGraph on startup.
    """
    print("🚀 Starting OrientAgent API...")
    
    # Initialize ChromaDB (lazy, but verify it's set up)
    chroma_path = os.getenv("CHROMA_DB_PATH", "./rag/chroma_db")
    if not os.path.exists(chroma_path):
        print(f"⚠️  ChromaDB not found at {chroma_path}. Run 'python rag/indexer.py' first.")
    else:
        print(f"✓ ChromaDB found at {chroma_path}")
    
    # Initialize the LangGraph (compiles on first use)
    try:
        from graph.graph import get_graph
        _ = get_graph()
        print("✓ LangGraph compiled successfully")
    except Exception as e:
        print(f"⚠️  LangGraph compilation warning: {e}")
    
    # Create data directories
    os.makedirs("./data/reports", exist_ok=True)
    print("✓ Data directories ready")
    
    print("✅ OrientAgent API ready!\n")
    
    yield
    
    print("\n👋 Shutting down OrientAgent API...")


app = FastAPI(
    title="OrientAgent API",
    description="""
    Multi-agent AI system for Moroccan student orientation.
    
    ## Features
    - **Profile Analysis**: Analyzes student academic profile and interests
    - **RAG-powered Search**: Retrieves relevant filières from verified knowledge base
    - **Personalized Recommendations**: Top 3 filières with action plans
    - **Interview Simulation**: Practice with AI-generated questions
    - **PDF Reports**: Downloadable personalized orientation report
    
    ## Agents
    1. **Profileur** - Analyzes profile and calculates domain scores
    2. **Explorateur** - Retrieves filières using RAG + Tavily
    3. **Conseiller** - Generates top 3 recommendations
    4. **Coach Entretien** - Simulates admission interviews
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
allowed_origins = [
    frontend_url,
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(session.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the API status and service availability.
    """
    services = {}
    
    # Check ChromaDB
    chroma_path = os.getenv("CHROMA_DB_PATH", "./rag/chroma_db")
    services["chromadb"] = "healthy" if os.path.exists(chroma_path) else "not_initialized"
    
    # Check GROQ API key services["groq"] = "configured" if os.getenv("GROQ_API_KEY") else "missing"
    
    # Check Tavily API key
    services["tavily"] = "configured" if os.getenv("TAVILY_API_KEY") else "missing"
    
    # Check SQLite
    sqlite_path = os.getenv("SQLITE_DB_PATH", "./data/orient_agent.db")
    services["sqlite"] = "healthy" if os.path.exists(os.path.dirname(sqlite_path)) else "not_initialized"
    
    overall_status = "healthy" if all(
        v in ["healthy", "configured"] for v in services.values()
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        services=services,
    )


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "OrientAgent API",
        "version": "1.0.0",
        "description": "Multi-agent AI system for Moroccan student orientation",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "start_session": "POST /api/session/start",
            "session_status": "GET /api/session/{id}/status",
            "session_result": "GET /api/session/{id}/result",
            "download_pdf": "GET /api/session/{id}/pdf",
            "select_filiere": "POST /api/session/{id}/select-filiere",
            "submit_answer": "POST /api/session/{id}/interview/answer",
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
