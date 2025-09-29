from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from . import models, deps, graph
from .models import Base
from .connectors import pubmed
from fastapi.middleware.cors import CORSMiddleware
import os

class HypothesisRequest(BaseModel):
    text: str

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/api/health")
def health_check(db: Session = Depends(deps.get_db)):
    try:
        # to check database connection
        db.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

@app.get("/api/debug-env")
def debug_env():
    return {
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY"),
        "CEREBRAS_API_URL": os.getenv("CEREBRAS_API_URL"),
    }

@app.get("/api/search")
def search(query: str, db: Session = Depends(deps.get_db)):
    """
    Performs a literature search using the PubMed connector.
    """
    if not query:
        raise HTTPException(status_code=400, detail="A search query is required.")

    results = pubmed.search_pubmed(query)
    return {"query": query, "results": results}

@app.post("/api/hypothesis")
def generate_hypothesis(request: HypothesisRequest, db: Session = Depends(deps.get_db)):
    """
    Generates a hypothesis using the graph simulation.
    """
    hypothesis = graph.generate_hypothesis_from_graph(request.dict())
    return {"hypothesis": hypothesis}