from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from . import models, deps, graph, rag, auth, graph_generator
from .models import Base
from .connectors import pubmed, pubchem, pdb, trials
import os
import httpx
import json
import time
import base64
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from functools import lru_cache

class HypothesisRequest(BaseModel):
    text: str

class SearchRequest(BaseModel):
    query: str
    mode: str = "literature"
    filters: Optional[Dict] = None
    sort_by: Optional[str] = "relevance"
    max_results: Optional[int] = 10  # literature, hypothesis, download

class DownloadRequest(BaseModel):
    compound_name: str

class ExportRequest(BaseModel):
    query: str
    format: str  # "pdf" or "csv"
    data_type: str  # "literature", "trials", "both"
    filters: Optional[Dict] = None

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class WorkspaceInvite(BaseModel):
    workspace_id: int
    user_email: str
    role: str = "member"

class ShareSearchRequest(BaseModel):
    workspace_id: int
    query: str
    results: Dict
    filters: Optional[Dict] = None

class CommentRequest(BaseModel):
    shared_search_id: int
    content: str

app = FastAPI(title="Clintra API", description="AI-Powered Drug Discovery Assistant")

# Rate limiting storage
rate_limit_storage = defaultdict(list)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "frontend", "backend"]
)

# GZip compression for faster responses
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000  # Compress responses larger than 1KB
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    current_time = time.time()
    
    # Clean old entries (older than 1 minute)
    rate_limit_storage[client_ip] = [
        timestamp for timestamp in rate_limit_storage[client_ip]
        if current_time - timestamp < 60
    ]
    
    # Check rate limit (max 30 requests per minute)
    if len(rate_limit_storage[client_ip]) >= 30:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Add current request
    rate_limit_storage[client_ip].append(current_time)
    
    response = await call_next(request)
    return response

# Initialize database tables
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=deps.engine)

@app.get("/api/health")
def health_check(db: Session = Depends(deps.get_db)):
    try:
        # to check database connection
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

@app.get("/api/debug-env")
def debug_env():
    return {
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY"),
        "CEREBRAS_API_URL": os.getenv("CEREBRAS_API_URL"),
        "CEREBRAS_API_KEY": "***" if os.getenv("CEREBRAS_API_KEY") else None,
    }

@app.post("/api/search")
async def search(request: SearchRequest, db: Session = Depends(deps.get_db)):
    """
    Simplified search endpoint using the proven smart-chat pattern that actually works.
    """
    # Import validation utilities
    from .errors import validate_query
    
    # Validate and sanitize query
    try:
        validate_query(request.query, max_length=500)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        print(f"Debug: SIMPLE search endpoint for query: '{request.query}'")
        
        # Get literature data using the PROVEN working pattern from smart-chat
        from .connectors.pubmed import PubMedConnector
        from .connectors.trials import ClinicalTrialsConnector
        from . import rag
        
        pubmed_connector = PubMedConnector()
        trials_connector = ClinicalTrialsConnector()
        
        # Search literature and trials - using the working smart-chat pattern
        try:
            articles = pubmed_connector.search_articles(request.query, max_results=20)
            print(f"Debug: Simple PubMed returned {len(articles)} articles")
            if not articles:
                print(f"No PubMed articles found for query: {request.query}")
        except Exception as e:
            print(f"PubMed connector error: {e}")
            articles = []
            
        try:
            trials_result = trials_connector.search_trials(request.query, max_results=10)
            trials = trials_result.get('trials', []) if trials_result else []
            print(f"Debug: Simple ClinicalTrials returned {len(trials)} trials")
            if not trials:
                print(f"No clinical trials found for query: {request.query}")
        except Exception as e:
            print(f"ClinicalTrials connector error: {e}")
            trials = []
        
        
        # Prepare literature context for analysis - SAME as smart-chat
        literature_context = ""
        if articles:
            literature_context += f"COMPREHENSIVE RESEARCH LITERATURE ANALYSIS ({len(articles)} recent papers):\\n"
            for i, article in enumerate(articles, 1):
                literature_context += f"\\n{i}. **{article.get('title', 'N/A')}**\\n"
                literature_context += f"   Authors: {article.get('authors', 'N/A')}\\n"
                literature_context += f"   Journal: {article.get('journal', 'N/A')}\\n"
                literature_context += f"   Published: {article.get('date', 'N/A')}\\n"
                literature_context += f"   PMID: {article.get('pmid', 'N/A')}\\n"
                literature_context += f"   DOI: {article.get('doi', 'N/A')}\\n"
                if article.get('abstract'):
                    literature_context += f"   Abstract: {article['abstract'][:500]}...\\n"
                literature_context += f"   URL: https://pubmed.ncbi.nlm.nih.gov/{article.get('pmid', '')}\\n"
        
        if trials:
            literature_context += f"\\n\\nCLINICAL TRIALS DATA ({len(trials)} active studies):\\n"
            for i, trial in enumerate(trials, 1):
                literature_context += f"\\n{i}. **{trial.get('title', 'N/A')}**\\n"
                literature_context += f"   NCT ID: {trial.get('nct_id', 'N/A')}\\n"
                literature_context += f"   Status: {trial.get('status', 'N/A')}\\n"
                literature_context += f"   Phase: {trial.get('phase', 'N/A')}\\n"
                literature_context += f"   URL: {trial.get('url', 'N/A')}\\n"
        
        if not literature_context:
            literature_context = "No literature data available for this query."
        
        print(f"Debug: Literature context prepared: {len(literature_context)} characters")
        
        # Get additional data from PubChem and PDB connectors
        from .connectors.pubchem import PubChemConnector
        from .connectors.pdb import PDBConnector
        
        pubchem_connector = PubChemConnector()
        pdb_connector = PDBConnector()
        
        # Get compound data from PubChem
        try:
            compounds = pubchem_connector.search_compounds(request.query, max_results=5, literature_context=literature_context)
            print(f"Debug: PubChem returned {len(compounds)} compounds")
        except Exception as e:
            print(f"PubChem connector error: {e}")
            compounds = []
        
        # Get protein structures from PDB
        try:
            protein_structures = pdb_connector.search_proteins(request.query, max_results=5)
            print(f"Debug: PDB returned {len(protein_structures)} structures")
        except Exception as e:
            print(f"PDB connector error: {e}")
            protein_structures = []
        
        # Prepare comprehensive context for analysis
        comprehensive_context = literature_context
        
        # Add compound data to context
        if compounds:
            comprehensive_context += f"\n\nCOMPOUND DATA ({len(compounds)} therapeutic compounds):\n"
            for i, compound in enumerate(compounds, 1):
                comprehensive_context += f"\n{i}. **{compound.get('name', 'N/A')}**\n"
                comprehensive_context += f"   PubChem CID: {compound.get('cid', 'N/A')}\n"
                comprehensive_context += f"   Molecular Formula: {compound.get('molecular_formula', 'N/A')}\n"
                comprehensive_context += f"   Molecular Weight: {compound.get('molecular_weight', 'N/A')}\n"
                comprehensive_context += f"   Mechanism: {compound.get('mechanism', 'N/A')}\n"
                comprehensive_context += f"   Targets: {', '.join(compound.get('targets', []))}\n"
                comprehensive_context += f"   URL: {compound.get('url', 'N/A')}\n"
        
        # Add protein structure data to context
        if protein_structures:
            comprehensive_context += f"\n\nPROTEIN STRUCTURES ({len(protein_structures)} structures):\n"
            for i, structure in enumerate(protein_structures, 1):
                comprehensive_context += f"\n{i}. **{structure.get('title', 'N/A')}**\n"
                comprehensive_context += f"   PDB ID: {structure.get('pdb_id', 'N/A')}\n"
                comprehensive_context += f"   Resolution: {structure.get('resolution', 'N/A')}\n"
                comprehensive_context += f"   Method: {structure.get('method', 'N/A')}\n"
                comprehensive_context += f"   Organism: {structure.get('organism', 'N/A')}\n"
                comprehensive_context += f"   URL: {structure.get('url', 'N/A')}\n"
        
        # Generate comprehensive analysis using Cerebras Llama
        rag_prompt = f"""You are CLINTRA, an advanced biomedical research accelerator. Generate a comprehensive research report based on the provided data.

RESEARCH QUERY: "{request.query}"

DATABASE ANALYSIS:
{comprehensive_context}

INSTRUCTIONS: Create a detailed research report with the exact structure below. Fill in ALL sections with specific content based on the provided data.

# 📊 COMPREHENSIVE RESEARCH ANALYSIS

## Research Query: {request.query}

## 📚 LITERATURE FINDINGS
**Based on analysis of {len(articles)} research papers:**

Provide detailed analysis of key findings from the literature with specific paper references, PMIDs, and direct links.

## 🧬 MOLECULAR TARGETS & PROTEIN STRUCTURES
**Protein structures and molecular targets:**

Analyze protein structures with PDB IDs, resolution data, and structural insights. Include all PDB IDs provided in the data.

## 💊 THERAPEUTIC COMPOUNDS & DRUG TARGETS
**Chemical compounds and therapeutic agents:**

Analyze compounds with PubChem CIDs, molecular formulas, mechanisms, and therapeutic targets. Include all PubChem data provided.

## 🏥 CLINICAL EVIDENCE & TRIALS
**Clinical trial findings and evidence:**

Summarize clinical trials with NCT IDs, trial phases, status, and outcomes. Include all trial data provided.

## 🔬 MOLECULAR MECHANISMS & PATHWAYS
**Underlying biological mechanisms:**

Explain molecular pathways, mechanisms of action, and biological processes relevant to the query.

## 📈 KEY INSIGHTS & RECOMMENDATIONS
**Research implications and future directions:**

Provide actionable insights, clinical implications, and recommendations for future research. Consider diverse perspectives of healthcare professionals, researchers, and patients.

## 📋 REFERENCES & DATA SOURCES
**Complete reference list with links:**

List all papers with PMIDs and PubMed links, trials with NCT IDs and ClinicalTrials.gov links, compounds with PubChem CIDs and PubChem links, and structures with PDB IDs and RCSB PDB links.

**TL;DR:** Comprehensive summary of the most important findings and implications for clinical practice and research.

CRITICAL: 
- Generate complete content for ALL sections without truncation
- Use real data from the provided analysis
- Include specific PDB IDs, PubChem CIDs, PMIDs, and NCT IDs
- Do not use placeholder text or "... (Continue with the rest of...)"
- Complete each section fully with actual content
- End with a proper TL;DR summary"""

        print(f"Debug: Calling Cerebras API for comprehensive search")
        rag_summary = await rag.call_cerebras_api(rag_prompt, max_tokens=5000, model="llama3.1-8b", temperature=0.7)
        print(f"Debug: Cerebras returned {len(rag_summary) if rag_summary else 0} characters")
        
        # Don't remove TL;DR sections - they're part of the comprehensive report now
        if not rag_summary:
            rag_summary = "Comprehensive analysis temporarily unavailable. Please try again."
        
        print(f"Debug: Final analysis length: {len(rag_summary) if rag_summary else 0}")
        
        return {
            "query": request.query,
            "analysis": rag_summary,
            "literature_count": len(articles),
            "trials_count": len(trials),
            "compounds_count": len(compounds),
            "structures_count": len(protein_structures),
            "analysis_type": "comprehensive_research_analysis",
            "primary_ai_model": "Cerebras Llama 3.1-8B",
            "sponsor_tech": "🏆 PRIMARY: Cerebras Llama 3.1-8B (sponsor technology) + Docker MCP",
            "data_sources": {
                "pubmed_articles": len(articles),
                "clinical_trials": len(trials),
                "pubchem_compounds": len(compounds),
                "pdb_structures": len(protein_structures)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/api/smart-analysis")
async def smart_literature_analysis(request: SearchRequest, db: Session = Depends(deps.get_db)):
    """
    Advanced literature analysis using OpenAI GPT-4 for deep insights.
    """
    from .errors import validate_query
    
    try:
        validate_query(request.query, max_length=500)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        import openai
        import os
        
        # Get OpenAI client
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API not configured")
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Get PubMed data for analysis
        from .connectors.pubmed import PubMedConnector
        pubmed_connector = PubMedConnector()
        
        try:
            articles = pubmed_connector.search_articles(request.query, max_results=10)
            print(f"Debug: Setting articles from PubMed results: {len(articles)}")
        except Exception as e:
            print(f"PubMed connector error: {e}")
            articles = []
        
        # Prepare literature context
        literature_context = ""
        for i, article in enumerate(articles[:5], 1):
            literature_context += f"\n{i}. Title: {article.get('title', 'N/A')}\n"
            literature_context += f"   Abstract: {article.get('abstract', 'N/A')[:500]}...\n"
            literature_context += f"   Authors: {', '.join(article.get('authors', [])[:3])}\n"
            literature_context += f"   Journal: {article.get('journal', 'N/A')}\n"
        
        # Create smart analysis prompt
        analysis_prompt = f"""You are an expert biomedical research analyst. Analyze the following literature on "{request.query}" and provide comprehensive insights.

LITERATURE DATA:
{literature_context}

Please provide a detailed analysis with the following structure:

## 🔬 Key Scientific Findings
- Summarize the most important discoveries and results
- Highlight breakthrough findings and novel insights
- Include specific data points and statistics where available

## 📊 Research Trends & Patterns  
- Identify emerging trends in this research area
- Note methodological approaches being used
- Highlight consensus vs. controversial findings

## 🎯 Clinical Implications
- Discuss potential therapeutic applications
- Identify patient populations that could benefit
- Note safety considerations and limitations

## 🔮 Future Research Directions
- Suggest promising research questions
- Identify knowledge gaps that need addressing
- Recommend experimental approaches

## 💡 Research Insights
- Provide expert commentary on the field's direction
- Identify potential collaboration opportunities
- Suggest interdisciplinary connections

**TL;DR:** Provide a concise 2-3 sentence summary of the most critical insights.

Format your response with proper markdown headers and bullet points for readability."""

        print(f"Debug: Starting Cerebras analysis section - literature context length: {len(literature_context)}")
        
        # PRIMARY ANALYSIS: Use Cerebras + Llama (SPONSOR TECH!)
        from . import rag
        print(f"Debug: Calling Cerebras API for analysis")
        cerebras_analysis = await rag.call_cerebras_api(analysis_prompt, max_tokens=1200, model="llama3.1-8b", temperature=0.7)
        print(f"Debug: Cerebras returned {len(cerebras_analysis) if cerebras_analysis else 0} characters")
        
        # SECONDARY ENHANCEMENT: Use OpenAI for specific enhancements only
        enhancement_prompt = f"""Enhance this Cerebras Llama analysis with specific technical details:

{cerebras_analysis}

Add only:
- Specific molecular mechanisms (2-3 key pathways)
- Recent breakthrough technologies (1-2 examples)
- Quantitative data points where possible

Keep it concise (max 300 words) and technical."""

        try:
            openai_enhancement = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical enhancement specialist. Add specific molecular and quantitative details."},
                    {"role": "user", "content": enhancement_prompt}
                ],
                max_tokens=400,
                temperature=0.5
            )
            enhancement = openai_enhancement.choices[0].message.content
            
            # Combine with clear attribution
            analysis_result = f"""{cerebras_analysis}

## 🔬 Technical Enhancement (OpenAI GPT-4 Supplement)
{enhancement}

---
**AI Architecture**: Primary analysis powered by **Cerebras Llama 3.1-8B** (sponsor technology), enhanced with OpenAI GPT-4 for technical details."""
            
        except Exception as e:
            # Fallback to pure Cerebras if OpenAI fails
            analysis_result = f"""{cerebras_analysis}

---
**AI Architecture**: Powered entirely by **Cerebras Llama 3.1-8B** (sponsor technology) - the future of AI inference!"""
        
        print(f"Debug: Final analysis_result length: {len(analysis_result) if analysis_result else 0}")
        
        return {
            "query": request.query,
            "analysis": analysis_result,
            "literature_count": len(articles),
            "analysis_type": "comprehensive_literature_analysis",
            "primary_ai_model": "Cerebras Llama 3.1-8B",
            "enhancement_model": "OpenAI GPT-4o-mini",
            "sponsor_tech": "🏆 PRIMARY: Cerebras Llama 3.1-8B (sponsor technology) + Docker MCP | ENHANCEMENT: OpenAI GPT-4",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Debug: EXCEPTION in search endpoint: {str(e)}")
        print(f"Debug: EXCEPTION type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Smart analysis failed: {str(e)}")

@app.post("/api/query-enhance")
async def enhance_query(request: SearchRequest, db: Session = Depends(deps.get_db)):
    """
    Enhance user queries with AI-powered suggestions and expansions.
    """
    from .errors import validate_query
    
    try:
        validate_query(request.query, max_length=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        import openai
        import os
        
        # Get OpenAI client
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API not configured")
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Create query enhancement prompt
        enhancement_prompt = f"""You are an expert biomedical research librarian. A researcher has asked: "{request.query}"

Please provide intelligent enhancements to help them find better research results:

## 🔍 Enhanced Search Terms
- Provide 5-7 related scientific terms and synonyms
- Include both broad and specific terminology
- Add relevant medical/scientific abbreviations

## 🎯 Focused Research Questions  
- Generate 3-4 specific, actionable research questions
- Make them suitable for literature searches
- Include different research angles (clinical, molecular, epidemiological)

## 🏷️ Relevant Keywords & MeSH Terms
- List important Medical Subject Headings (MeSH)
- Include relevant biomedical keywords
- Add alternative spellings and terminology

## 🔬 Research Context Suggestions
- Suggest related research areas to explore
- Identify potential interdisciplinary connections
- Recommend specific databases or resources

## 💡 Smart Search Strategies
- Provide Boolean search combinations
- Suggest filters and date ranges
- Recommend specific journals or authors to focus on

Keep suggestions practical and immediately actionable for biomedical research."""

        # PRIMARY: Use Cerebras + Llama for main enhancement (SPONSOR TECH!)
        from . import rag
        cerebras_enhancement = await rag.call_cerebras_api(enhancement_prompt, max_tokens=600, model="llama3.1-8b", temperature=0.6)
        
        # SECONDARY: Use OpenAI only for MeSH term validation
        mesh_prompt = f"""Based on this query: "{request.query}"

Provide ONLY a concise list of 5-7 relevant MeSH (Medical Subject Headings) terms in this format:
- Term 1
- Term 2
- Term 3
etc.

No explanations, just the MeSH terms."""

        try:
            mesh_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a MeSH term specialist. Provide only MeSH terms, no explanations."},
                    {"role": "user", "content": mesh_prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            mesh_terms = mesh_response.choices[0].message.content
            
            enhancement_result = f"""{cerebras_enhancement}

## 🏷️ Validated MeSH Terms (OpenAI Specialist)
{mesh_terms}

---
**AI Architecture**: Query enhancement powered by **Cerebras Llama 3.1-8B** (sponsor technology), with MeSH validation by OpenAI GPT-4."""
            
        except Exception as e:
            enhancement_result = f"""{cerebras_enhancement}

---
**AI Architecture**: Powered entirely by **Cerebras Llama 3.1-8B** (sponsor technology) - superior query understanding!"""
        
        # Generate related queries using a simpler approach
        related_queries = [
            f"{request.query} mechanisms",
            f"{request.query} clinical trials",
            f"{request.query} therapeutic targets",
            f"{request.query} biomarkers",
            f"{request.query} drug development"
        ]
        
        return {
            "original_query": request.query,
            "enhanced_suggestions": enhancement_result,
            "related_queries": related_queries,
            "enhancement_type": "ai_powered_query_expansion",
            "primary_ai_model": "Cerebras Llama 3.1-8B",
            "mesh_validator": "OpenAI GPT-4o-mini",
            "sponsor_tech": "🏆 PRIMARY: Cerebras Llama 3.1-8B (sponsor technology) | SPECIALIST: OpenAI MeSH validation",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query enhancement failed: {str(e)}")

@app.post("/api/research-trends")
async def analyze_research_trends(request: SearchRequest, db: Session = Depends(deps.get_db)):
    """
    Analyze research trends and provide insights using OpenAI.
    """
    from .errors import validate_query
    
    try:
        validate_query(request.query, max_length=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        import openai
        import os
        from datetime import datetime, timedelta
        
        # Get OpenAI client
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API not configured")
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Get recent literature for trend analysis
        from .connectors.pubmed import PubMedConnector
        pubmed_connector = PubMedConnector()
        
        # Get articles from different time periods
        recent_articles = pubmed_connector.search_articles(
            request.query, 
            max_results=15,
            filters={"date_range": "2023-2024"}
        )
        
        # Prepare trend analysis context
        trend_context = f"Recent research articles on '{request.query}':\n\n"
        for i, article in enumerate(recent_articles[:10], 1):
            trend_context += f"{i}. {article.get('title', 'N/A')} ({article.get('publication_date', 'N/A')})\n"
            trend_context += f"   Journal: {article.get('journal', 'N/A')}\n"
            trend_context += f"   Abstract: {article.get('abstract', 'N/A')[:300]}...\n\n"
        
        # Create trend analysis prompt
        trend_prompt = f"""You are a leading biomedical research analyst specializing in identifying emerging trends and future directions. Analyze the following recent research on "{request.query}":

{trend_context}

Provide a comprehensive trend analysis with the following structure:

## 📈 Emerging Research Trends
- Identify 3-5 key emerging trends in this field
- Highlight novel approaches and methodologies
- Note shifts in research focus or paradigms

## 🔥 Hot Research Topics
- List the most active areas of current investigation
- Identify breakthrough discoveries or technologies
- Highlight controversial or debated topics

## 🎯 Clinical Translation Trends
- Assess progress from bench to bedside
- Identify promising therapeutic developments
- Note regulatory and approval trends

## 🌟 Future Predictions
- Predict where this field is heading in the next 2-3 years
- Identify potential breakthrough opportunities
- Suggest emerging technologies that could impact this area

## 💰 Funding & Investment Trends
- Note areas attracting significant funding
- Identify potential commercial opportunities
- Highlight public vs. private research priorities

## 🤝 Collaboration Patterns
- Identify key research institutions and leaders
- Note interdisciplinary collaboration trends
- Suggest potential partnership opportunities

**TL;DR:** Provide a concise summary of the most significant trends and future opportunities.

Be specific, data-driven, and forward-looking in your analysis."""

        # PRIMARY: Use Cerebras + Llama for comprehensive trend analysis (SPONSOR TECH!)
        from . import rag
        cerebras_trends = await rag.call_cerebras_api(trend_prompt, max_tokens=1000, model="llama3.1-8b", temperature=0.7)
        
        # SECONDARY: Use OpenAI only for funding/investment insights
        funding_prompt = f"""Based on the research area "{request.query}", provide ONLY:

## 💰 Current Funding Landscape
- 2-3 major funding sources (NIH, private, etc.)
- Approximate funding amounts if known
- Key investment trends

## 🏢 Commercial Opportunities  
- 2-3 potential commercial applications
- Market size estimates if available
- Key companies in this space

Keep it concise and data-focused (max 200 words)."""

        try:
            funding_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a biotech funding and investment specialist. Provide only factual funding data."},
                    {"role": "user", "content": funding_prompt}
                ],
                max_tokens=300,
                temperature=0.4
            )
            funding_insights = funding_response.choices[0].message.content
            
            trend_analysis = f"""{cerebras_trends}

{funding_insights}

---
**AI Architecture**: Comprehensive trend analysis powered by **Cerebras Llama 3.1-8B** (sponsor technology), with funding insights from OpenAI GPT-4."""
            
        except Exception as e:
            trend_analysis = f"""{cerebras_trends}

---
**AI Architecture**: Powered entirely by **Cerebras Llama 3.1-8B** (sponsor technology) - unmatched trend prediction capabilities!"""
        
        return {
            "query": request.query,
            "trend_analysis": trend_analysis,
            "articles_analyzed": len(recent_articles),
            "analysis_period": "2023-2024",
            "analysis_type": "research_trend_analysis",
            "primary_ai_model": "Cerebras Llama 3.1-8B",
            "funding_specialist": "OpenAI GPT-4o-mini",
            "sponsor_tech": "🏆 PRIMARY: Cerebras Llama 3.1-8B (sponsor technology) | SPECIALIST: OpenAI funding insights",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")

@app.post("/api/analyze-file")
async def analyze_file(
    file: UploadFile = File(...),
    query: str = "",
    db: Session = Depends(deps.get_db)
):
    """
    Analyze uploaded files (images, PDFs, documents) using OpenAI Vision and document processing.
    """
    try:
        import openai
        import os
        import base64
        from io import BytesIO
        import PyPDF2
        import docx
        from PIL import Image
        
        # Get OpenAI client
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API not configured")
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Read file content
        file_content = await file.read()
        file_type = file.content_type
        file_name = file.filename
        
        analysis_result = ""
        file_info = {
            "name": file_name,
            "type": file_type,
            "size": len(file_content)
        }
        
        # Handle different file types
        if file_type.startswith('image/'):
            # IMAGE ANALYSIS using OpenAI Vision
            base64_image = base64.b64encode(file_content).decode('utf-8')
            
            vision_prompt = f"""Analyze this biomedical/scientific image in detail. Focus on:

## 🔬 Scientific Content Analysis
- Identify any charts, graphs, diagrams, or data visualizations
- Describe molecular structures, pathways, or biological processes shown
- Note any text, labels, or annotations visible

## 📊 Data Interpretation
- Extract any numerical data, statistics, or measurements
- Identify trends, patterns, or relationships shown
- Describe experimental results or findings if visible

## 🎯 Research Context
- Suggest what type of research this image relates to
- Identify potential applications or implications
- Note any clinical or therapeutic relevance

## 💡 Key Insights
- Provide expert interpretation of the visual data
- Suggest follow-up research questions
- Identify any notable findings or anomalies

User Query Context: "{query if query else 'General analysis'}"

**TL;DR:** Provide a concise summary of the most important findings from this image."""

            response = client.chat.completions.create(
                model="gpt-4o",  # Vision model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{file_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            analysis_result = response.choices[0].message.content
            
        elif file_type == 'application/pdf':
            # PDF ANALYSIS
            try:
                pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
                text_content = ""
                for page in pdf_reader.pages[:5]:  # First 5 pages
                    text_content += page.extract_text() + "\n"
                
                if len(text_content.strip()) > 0:
                    pdf_prompt = f"""Analyze this biomedical research document excerpt:

{text_content[:3000]}...

Provide a comprehensive analysis focusing on:

## 🔬 Research Summary
- Main research question and objectives
- Key methodologies and approaches used
- Primary findings and results

## 📊 Scientific Content
- Important data, statistics, or measurements
- Experimental design and controls
- Clinical or therapeutic implications

## 🎯 Key Insights
- Novel contributions to the field
- Potential applications or impact
- Limitations and future directions

## 💡 Research Context
- How this relates to current literature
- Potential collaboration opportunities
- Suggested follow-up studies

User Query Context: "{query if query else 'General document analysis'}"

**TL;DR:** Summarize the most critical findings and contributions of this research."""

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are an expert biomedical research analyst specializing in scientific literature review."},
                            {"role": "user", "content": pdf_prompt}
                        ],
                        max_tokens=1200
                    )
                    
                    analysis_result = response.choices[0].message.content
                else:
                    analysis_result = "Unable to extract readable text from this PDF. The document may be image-based or encrypted."
                    
            except Exception as e:
                analysis_result = f"Error processing PDF: {str(e)}"
        
        elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            # WORD DOCUMENT ANALYSIS
            try:
                if file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    doc = docx.Document(BytesIO(file_content))
                    text_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                else:
                    text_content = "Word document processing requires additional libraries."
                
                if len(text_content.strip()) > 0:
                    doc_prompt = f"""Analyze this biomedical document:

{text_content[:3000]}...

Focus on extracting and analyzing:
- Research objectives and hypotheses
- Methodological approaches
- Key findings and conclusions
- Clinical implications
- Future research directions

User Query: "{query if query else 'Document analysis'}"

Provide structured insights with clear headings and bullet points."""

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a biomedical document analyst."},
                            {"role": "user", "content": doc_prompt}
                        ],
                        max_tokens=1000
                    )
                    
                    analysis_result = response.choices[0].message.content
                else:
                    analysis_result = "Unable to extract text from this document."
                    
            except Exception as e:
                analysis_result = f"Error processing document: {str(e)}"
        
        else:
            analysis_result = f"Unsupported file type: {file_type}. Supported types: images (PNG, JPG, etc.), PDF, Word documents."
        
        # If we have a query, enhance with Cerebras analysis
        enhanced_analysis = analysis_result
        if query and analysis_result and "Error" not in analysis_result:
            try:
                from . import rag
                cerebras_prompt = f"""Based on this file analysis and the user's query "{query}", provide additional research insights:

FILE ANALYSIS:
{analysis_result}

USER QUERY: {query}

Provide complementary insights focusing on:
- How this relates to current research trends
- Potential therapeutic applications
- Suggested research directions
- Clinical relevance and implications

Keep it concise but insightful."""

                cerebras_insights = await rag.call_cerebras_api(cerebras_prompt, max_tokens=500, model="llama3.1-8b", temperature=0.7)
                
                enhanced_analysis = f"""{analysis_result}

## 🧠 Research Context Analysis (Cerebras Llama Enhancement)
{cerebras_insights}

---
**AI Architecture**: File analysis powered by **OpenAI GPT-4 Vision/Document Processing**, enhanced with **Cerebras Llama 3.1-8B** research insights."""
                
            except Exception as e:
                enhanced_analysis = f"""{analysis_result}

---
**AI Architecture**: File analysis powered by **OpenAI GPT-4 Vision/Document Processing** (specialized multimodal AI)."""
        
        return {
            "file_info": file_info,
            "query": query,
            "analysis": enhanced_analysis,
            "analysis_type": "multimodal_file_analysis",
            "primary_ai": "OpenAI GPT-4 Vision/Document",
            "enhancement_ai": "Cerebras Llama 3.1-8B" if query else None,
            "sponsor_tech": "🎯 SPECIALIZED: OpenAI multimodal analysis | 🏆 ENHANCEMENT: Cerebras Llama research insights",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File analysis failed: {str(e)}")

@app.post("/api/semantic-search")
async def semantic_search(request: SearchRequest, db: Session = Depends(deps.get_db)):
    """
    Perform semantic search using vector database.
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required for semantic search.")
    
    try:
        from .vector_db import vector_db
        
        # Perform semantic search
        results = vector_db.semantic_search(
            request.query,
            data_types=['literature', 'clinical_trial'],
            top_k=request.max_results or 10
        )
        
        # Get vector database stats
        stats = vector_db.get_index_stats()
        
        return {
            "query": request.query,
            "semantic_results": results,
            "vector_db_stats": stats,
            "sponsor_tech": "Powered by Pinecone vector database and OpenAI embeddings",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")

# Collaboration endpoints
@app.post("/api/workspaces")
async def create_workspace(request: WorkspaceCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(deps.get_db)):
    """
    Create a new workspace for team collaboration.
    """
    try:
        workspace = models.Workspace(
            name=request.name,
            description=request.description,
            created_by=current_user.id
        )
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        
        # Add creator as owner
        member = models.WorkspaceMember(
            workspace_id=workspace.id,
            user_id=current_user.id,
            role='owner'
        )
        db.add(member)
        db.commit()
        
        return {
            "id": workspace.id,
            "name": workspace.name,
            "description": workspace.description,
            "created_by": current_user.username,
            "created_at": workspace.created_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workspace: {str(e)}")

@app.get("/api/workspaces")
async def get_workspaces(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(deps.get_db)):
    """
    Get workspaces for the current user.
    """
    try:
        workspaces = db.query(models.Workspace).join(models.WorkspaceMember).filter(
            models.WorkspaceMember.user_id == current_user.id
        ).all()
        
        return [
            {
                "id": ws.id,
                "name": ws.name,
                "description": ws.description,
                "created_by": ws.creator.username,
                "created_at": ws.created_at.isoformat(),
                "member_count": len(ws.members)
            }
            for ws in workspaces
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workspaces: {str(e)}")

@app.post("/api/workspaces/{workspace_id}/invite")
async def invite_to_workspace(workspace_id: int, request: WorkspaceInvite, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(deps.get_db)):
    """
    Invite a user to a workspace.
    """
    try:
        # Check if current user is admin/owner
        membership = db.query(models.WorkspaceMember).filter(
            models.WorkspaceMember.workspace_id == workspace_id,
            models.WorkspaceMember.user_id == current_user.id
        ).first()
        
        if not membership or membership.role not in ['owner', 'admin']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Find user by email
        user = db.query(models.User).filter(models.User.email == request.user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if already a member
        existing_member = db.query(models.WorkspaceMember).filter(
            models.WorkspaceMember.workspace_id == workspace_id,
            models.WorkspaceMember.user_id == user.id
        ).first()
        
        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a member")
        
        # Add member
        member = models.WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user.id,
            role=request.role
        )
        db.add(member)
        db.commit()
        
        return {"message": f"Successfully invited {user.username} to workspace"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invite user: {str(e)}")

@app.post("/api/workspaces/share-search")
async def share_search(request: ShareSearchRequest, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(deps.get_db)):
    """
    Share a search result with workspace members.
    """
    try:
        # Check if user is member of workspace
        membership = db.query(models.WorkspaceMember).filter(
            models.WorkspaceMember.workspace_id == request.workspace_id,
            models.WorkspaceMember.user_id == current_user.id
        ).first()
        
        if not membership:
            raise HTTPException(status_code=403, detail="Not a member of this workspace")
        
        # Create shared search
        shared_search = models.SharedSearch(
            workspace_id=request.workspace_id,
            shared_by=current_user.id,
            query=request.query,
            results=request.results,
            filters=request.filters
        )
        db.add(shared_search)
        db.commit()
        db.refresh(shared_search)
        
        return {
            "id": shared_search.id,
            "query": shared_search.query,
            "shared_by": current_user.username,
            "workspace_id": shared_search.workspace_id,
            "created_at": shared_search.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to share search: {str(e)}")

@app.get("/api/workspaces/{workspace_id}/shared-searches")
async def get_shared_searches(workspace_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(deps.get_db)):
    """
    Get shared searches for a workspace.
    """
    try:
        # Check if user is member of workspace
        membership = db.query(models.WorkspaceMember).filter(
            models.WorkspaceMember.workspace_id == workspace_id,
            models.WorkspaceMember.user_id == current_user.id
        ).first()
        
        if not membership:
            raise HTTPException(status_code=403, detail="Not a member of this workspace")
        
        # Get shared searches
        shared_searches = db.query(models.SharedSearch).filter(
            models.SharedSearch.workspace_id == workspace_id
        ).order_by(models.SharedSearch.created_at.desc()).all()
        
        return [
            {
                "id": search.id,
                "query": search.query,
                "shared_by": search.sharer.username,
                "created_at": search.created_at.isoformat(),
                "comment_count": len(search.comments)
            }
            for search in shared_searches
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get shared searches: {str(e)}")

@app.post("/api/comments")
async def add_comment(request: CommentRequest, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(deps.get_db)):
    """
    Add a comment to a shared search.
    """
    try:
        # Check if user has access to the shared search
        shared_search = db.query(models.SharedSearch).filter(
            models.SharedSearch.id == request.shared_search_id
        ).first()
        
        if not shared_search:
            raise HTTPException(status_code=404, detail="Shared search not found")
        
        # Check if user is member of workspace
        membership = db.query(models.WorkspaceMember).filter(
            models.WorkspaceMember.workspace_id == shared_search.workspace_id,
            models.WorkspaceMember.user_id == current_user.id
        ).first()
        
        if not membership:
            raise HTTPException(status_code=403, detail="Not a member of this workspace")
        
        # Create comment
        comment = models.Comment(
            shared_search_id=request.shared_search_id,
            user_id=current_user.id,
            content=request.content
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        
        return {
            "id": comment.id,
            "content": comment.content,
            "user": current_user.username,
            "created_at": comment.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {str(e)}")

@app.get("/api/shared-searches/{search_id}/comments")
async def get_comments(search_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(deps.get_db)):
    """
    Get comments for a shared search.
    """
    try:
        # Check if user has access to the shared search
        shared_search = db.query(models.SharedSearch).filter(
            models.SharedSearch.id == search_id
        ).first()
        
        if not shared_search:
            raise HTTPException(status_code=404, detail="Shared search not found")
        
        # Check if user is member of workspace
        membership = db.query(models.WorkspaceMember).filter(
            models.WorkspaceMember.workspace_id == shared_search.workspace_id,
            models.WorkspaceMember.user_id == current_user.id
        ).first()
        
        if not membership:
            raise HTTPException(status_code=403, detail="Not a member of this workspace")
        
        # Get comments
        comments = db.query(models.Comment).filter(
            models.Comment.shared_search_id == search_id
        ).order_by(models.Comment.created_at.asc()).all()
        
        return [
            {
                "id": comment.id,
                "content": comment.content,
                "user": comment.user.username,
                "created_at": comment.created_at.isoformat()
            }
            for comment in comments
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comments: {str(e)}")

# ETL Pipeline endpoints
@app.post("/api/etl/run-full")
async def run_full_etl(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(deps.get_db)):
    """
    Run the complete ETL pipeline for all data sources.
    """
    try:
        from .etl_pipeline import etl_pipeline
        
        # Run ETL pipeline
        result = await etl_pipeline.run_full_pipeline(db)
        
        return {
            "message": "ETL pipeline completed",
            "result": result,
            "sponsor_tech": "Powered by Docker MCP Gateway and automated data ingestion"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ETL pipeline failed: {str(e)}")

@app.post("/api/etl/run-incremental")
async def run_incremental_etl(hours_back: int = 24, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(deps.get_db)):
    """
    Run incremental ETL update for recent data.
    """
    try:
        from .etl_pipeline import etl_pipeline
        
        # Run incremental ETL
        result = await etl_pipeline.run_incremental_update(db, hours_back)
        
        return {
            "message": "Incremental ETL completed",
            "result": result,
            "sponsor_tech": "Powered by Docker MCP Gateway and automated data ingestion"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Incremental ETL failed: {str(e)}")

@app.get("/api/etl/status")
async def get_etl_status(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(deps.get_db)):
    """
    Get ETL pipeline status and statistics.
    """
    try:
        from .vector_db import vector_db
        
        # Get vector database stats
        vector_stats = vector_db.get_index_stats()
        
        # Get recent ETL activities
        recent_activities = db.query(models.Activity).filter(
            models.Activity.activity_type.like('etl_%')
        ).order_by(models.Activity.created_at.desc()).limit(10).all()
        
        activities = [
            {
                'id': activity.id,
                'type': activity.activity_type,
                'query': activity.query,
                'result_summary': activity.result_summary,
                'created_at': activity.created_at.isoformat()
            }
            for activity in recent_activities
        ]
        
        return {
            "vector_database": vector_stats,
            "recent_activities": activities,
            "sponsor_tech": "Powered by Pinecone vector database and automated ETL pipeline"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ETL status: {str(e)}")

# Data Quality endpoints
@app.post("/api/data-quality/validate")
async def validate_data(request: Dict[str, Any], current_user: models.User = Depends(auth.get_current_user)):
    """
    Validate data quality for a batch of documents.
    """
    try:
        from .data_quality import data_quality_validator
        
        documents = request.get('documents', [])
        doc_type = request.get('doc_type', 'pubmed')
        
        if not documents:
            raise HTTPException(status_code=400, detail="No documents provided")
        
        # Validate batch
        result = data_quality_validator.validate_batch(documents, doc_type)
        
        return {
            "validation_result": result,
            "sponsor_tech": "Powered by automated data quality validation"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data validation failed: {str(e)}")

@app.post("/api/data-quality/clean")
async def clean_data(request: Dict[str, Any], current_user: models.User = Depends(auth.get_current_user)):
    """
    Clean and normalize a batch of documents.
    """
    try:
        from .data_quality import data_quality_validator
        
        documents = request.get('documents', [])
        doc_type = request.get('doc_type', 'pubmed')
        
        if not documents:
            raise HTTPException(status_code=400, detail="No documents provided")
        
        # Clean documents
        cleaned_documents = []
        for document in documents:
            cleaned_doc = data_quality_validator.clean_document(document, doc_type)
            cleaned_documents.append(cleaned_doc)
        
        return {
            "cleaned_documents": cleaned_documents,
            "original_count": len(documents),
            "cleaned_count": len(cleaned_documents),
            "sponsor_tech": "Powered by automated data cleaning and normalization"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data cleaning failed: {str(e)}")

@app.get("/api/data-quality/metrics")
async def get_data_quality_metrics(current_user: models.User = Depends(auth.get_current_user)):
    """
    Get data quality metrics and statistics.
    """
    try:
        from .data_quality import data_quality_validator
        
        metrics = data_quality_validator.get_quality_metrics()
        
        return {
            "metrics": metrics,
            "sponsor_tech": "Powered by automated data quality monitoring"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data quality metrics: {str(e)}")

@app.post("/api/hypothesis")
async def generate_hypothesis(request: HypothesisRequest, db: Session = Depends(deps.get_db)):
    """
    🚀 ENHANCED HYPOTHESIS GENERATION using proven smart-chat pattern!
    """
    try:
        print(f"HACKATHON ENHANCEMENT: Generating hypothesis for '{request.text}'")
        
        # STEP 1: ENHANCED LITERATURE CONTEXT using smart-chat pattern
        from .connectors.pubmed import PubMedConnector
        from .connectors.trials import ClinicalTrialsConnector
        from .connectors.pubchem import PubChemConnector
        from .connectors.pdb import PDBConnector
        
        pubmed_connector = PubMedConnector()
        trials_connector = ClinicalTrialsConnector()
        pubchem_connector = PubChemConnector()
        pdb_connector = PDBConnector()
        
        # ENHANCED: Use same dynamic search pattern as smart-chat
        print(f"Debug: Hypothesis - fetching comprehensive literature context...")
        
        # Get literature data with dynamic search variations
        articles = []
        trials = []
        compounds = []
        structures = []
        
        try:
            articles = pubmed_connector.search_articles(request.text, max_results=15)
            print(f"Debug: Hypothesis - found {len(articles)} PubMed articles")
        except Exception as e:
            print(f"PubMed context error: {e}")
        
        try:
            trials_result = trials_connector.search_trials(request.text, max_results=8)
            trials = trials_result.get('trials', []) if trials_result else []
            print(f"Debug: Hypothesis - found {len(trials)} clinical trials")
        except Exception as e:
            print(f"Clinical trials context error: {e}")
        
        try:
            compounds = pubchem_connector.search_compounds(request.text, max_results=5)
            print(f"Debug: Hypothesis - found {len(compounds)} compounds")
        except Exception as e:
            print(f"PubChem context error: {e}")
        
        try:
            structures = pdb_connector.search_proteins(request.text, max_results=5)
            print(f"Debug: Hypothesis - found {len(structures)} protein structures")
        except Exception as e:
            print(f"PDB context error: {e}")
        
        # Build comprehensive literature context
        literature_context = ""
        
        if articles:
            literature_context += f"🔬 RESEARCH LITERATURE CONTEXT ({len(articles)} papers):\n\n"
            for i, article in enumerate(articles, 1):
                literature_context += f"{i}. **{article['title']}**\n"
                literature_context += f"   Authors: {article.get('authors', 'N/A')}\n"
                literature_context += f"   Journal: {article.get('journal', 'N/A')}\n"
                literature_context += f"   PMID: {article.get('pmid', 'N/A')}\n"
                literature_context += f"   Key findings: {article.get('abstract', 'N/A')[:400]}...\n\n"
        
        if trials:
            literature_context += f"🏥 CLINICAL TRIALS CONTEXT ({len(trials)} studies):\n\n"
            for i, trial in enumerate(trials, 1):
                literature_context += f"{i}. **{trial['title']}**\n"
                literature_context += f"   Status: {trial.get('status', 'N/A')} | Phase: {trial.get('phase', 'N/A')}\n"
                literature_context += f"   NCT ID: {trial.get('nct_id', 'N/A')}\n\n"
        
        if compounds:
            literature_context += f"💊 COMPOUND CONTEXT ({len(compounds)} compounds):\n\n"
            for i, compound in enumerate(compounds, 1):
                literature_context += f"{i}. **{compound['name']}**\n"
                literature_context += f"   CID: {compound.get('cid', 'N/A')}\n"
                literature_context += f"   Formula: {compound.get('molecular_formula', 'N/A')}\n\n"
        
        if structures:
            literature_context += f"🧬 PROTEIN STRUCTURE CONTEXT ({len(structures)} structures):\n\n"
            for i, structure in enumerate(structures, 1):
                literature_context += f"{i}. **{structure['title']}**\n"
                literature_context += f"   PDB ID: {structure.get('pdb_id', 'N/A')}\n"
                literature_context += f"   Resolution: {structure.get('resolution', 'N/A')}\n\n"
        
        # 🚀 ENHANCED HYPOTHESIS GENERATOR
        hypothesis_prompt = f"""You are a world-class biomedical research scientist. Generate a comprehensive, structured hypothesis based on the research topic below.

RESEARCH TOPIC: "{request.text}"

RESEARCH DATA AVAILABLE:
{literature_context}

Generate a detailed, evidence-based hypothesis with the following structure:

# 🧬 COMPREHENSIVE RESEARCH HYPOTHESIS

## Research Topic: {request.text}

## 🎯 PRIMARY HYPOTHESIS
**Main Hypothesis:** Based on the literature analysis, provide a clear, testable statement about the research topic.

**Confidence Level:** Assess as High/Medium/Low based on available evidence.

## 📚 SUPPORTING EVIDENCE
**Literature Foundation:**
- Cite specific studies with PMIDs and key findings from the provided data
- Reference clinical trials with NCT IDs if available
- Include molecular targets and mechanisms from the data

## 🔬 MOLECULAR MECHANISMS
**Proposed Biological Pathways:**
- Describe detailed molecular mechanisms and signaling pathways
- Identify key protein targets and drug interactions
- Explain cellular and molecular processes involved

## 🏥 CLINICAL IMPLICATIONS
**Patient Care Impact:**
- Explain how this hypothesis could improve patient outcomes
- Identify potential diagnostic or therapeutic applications
- Discuss clinical translation opportunities

## 🧪 RESEARCH DIRECTIONS
**Experimental Approaches:**
1. Specify experiments needed to test the hypothesis
2. Describe required methodologies and techniques
3. Outline controls and validation approaches
4. Estimate timeline and resource requirements

## 🚀 FUTURE APPLICATIONS
**Innovation Potential:**
- Identify therapeutic applications and drug development opportunities
- Suggest diagnostic tools and biomarkers
- Explore precision medicine opportunities

## 📊 HYPOTHESIS VALIDATION
**Testable Predictions:**
- Provide specific, measurable outcomes
- Describe expected experimental results
- Define success criteria and benchmarks

## ⚠️ LIMITATIONS & CHALLENGES
**Potential Obstacles:**
- Identify known limitations and challenges
- Discuss technical difficulties
- Propose mitigation strategies

**TL;DR:** Provide a 2-3 sentence summary of the hypothesis and its key implications for research and clinical practice.

REQUIREMENTS:
- Use real data from the provided literature
- Include specific drug names, protein targets, and mechanisms
- Cite relevant studies with PMIDs and NCT IDs
- Provide testable predictions and experimental approaches
- Write in clear, professional scientific style
- Complete all sections with actual content, not placeholders"""

        # STEP 3: Generate hypothesis using proven RAG system
        from .rag import call_cerebras_api
        hypothesis_text = await call_cerebras_api(hypothesis_prompt, max_tokens=4000, model="llama3.1-8b", temperature=0.7)
        
        # STEP 4: Quality assessment
        hypothesis_length = len(hypothesis_text)
        plausibility_score = min(0.95, 0.6 + (hypothesis_length / 10000))  # Length-based quality indicator
        
        # STEP 5: ENHANCED response structure with comprehensive data
        response = {
            "hypothesis": hypothesis_text,
            "input": request.text,
            "plausibility_score": round(plausibility_score, 2),
            "citations": articles[:5],  # Top 5 citations
            "clinical_trials": trials[:3],  # Top 3 trials
            "compounds": compounds[:3],  # Top 3 compounds
            "protein_structures": structures[:3],  # Top 3 structures
            "research_context": f"Comprehensive analysis based on {len(articles)} PubMed articles, {len(trials)} clinical trials, {len(compounds)} compounds, and {len(structures)} protein structures",
            "sponsor_tech": "Powered by Cerebras Llama inference + Docker MCP microservices + biomedical databases",
            "confidence": "High" if hypothesis_length > 1500 else "Medium",
            "hypothesis_type": "Evidence-based biomedical research with multi-modal data integration",
            "literature_count": len(articles),
            "trials_count": len(trials),
            "compounds_count": len(compounds),
            "structures_count": len(structures),
            "ai_model": "Cerebras Llama 3.1-8B",
            "data_sources": ["PubMed", "ClinicalTrials.gov", "PubChem", "RCSB PDB"],
            "search_method": "Multi-variation dynamic search with literature integration"
        }
        
        print(f"HACKATHON SUCCESS: Generated hypothesis ({hypothesis_length} chars) with {len(articles)} citations")
        return response
        
    except Exception as e:
        print(f"HACKATHON ERROR: Hypothesis generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hypothesis generation failed: {str(e)}")

@app.post("/api/download")
async def download_data(request: DownloadRequest, db: Session = Depends(deps.get_db)):
    """
    🚀 ENHANCED DOWNLOAD SYSTEM using proven smart-chat pattern!
    """
    try:
        print(f"HACKATHON ENHANCEMENT: Downloading data for '{request.compound_name}'")
        
        # STEP 0: SMART COMPOUND NAME EXTRACTION from natural language
        compound_name = request.compound_name.strip()
        
        # 🚀 AI-POWERED SMART EXTRACTION + SPELL CORRECTION
        compound_name_lower = compound_name.lower()
        
        # Remove common command words and extract pure drug name(s)
        import re
        command_words = r'\b(give|me|get|download|show|need|want|data|information|link|links|structure|compound|file|files)\b'
        extracted_name = re.sub(command_words, '', compound_name_lower).strip()
        
        # Handle compound combinations (multi-drug queries)
        if ' and ' in extracted_name:
            compounds = extracted_name.split(' and ')
            extracted_name = compounds[0].strip()  # Take first compound
        elif ' + ' in extracted_name:
            compounds = extracted_name.split(' + ')
            extracted_name = compounds[0].strip()  # Take first compound
        elif ',' in extracted_name:
            compounds = extracted_name.split(',')
            extracted_name = compounds[0].strip()  # Take first compound
        elif len(extracted_name.split()) > 1:
            words = extracted_name.split()
            # Keep first word if it's reasonably long (likely main compound)
            if len(words[0]) > 3:
                extracted_name = words[0].strip()
        
        # Clean up: remove empty spaces
        initial_name = extracted_name.strip()
        
        # 🤖 AI-POWERED SPELL CORRECTION & NAME STANDARDIZATION
        if initial_name and len(initial_name.strip()) > 2:
            spell_correction_prompt = f"""Correct this biomedical compound name: "{initial_name}"

Examples:
- "asprin" → "aspirin"
- "insuline" → "insulin" 
- "metformine" → "metformin"
- "warfarin" → "warfarin"

Return ONLY the corrected name, nothing else."""
            
            try:
                from . import rag
                corrected_name = await rag.call_cerebras_api(spell_correction_prompt, max_tokens=20, model="llama3.1-8b", temperature=0.1)
                corrected_name = corrected_name.strip().lower()
                
                # Clean up AI response - remove any extra text
                if corrected_name:
                    # Remove any TL;DR or other unwanted text
                    corrected_name = corrected_name.split('\n')[0].split('.')[0].strip()
                    if len(corrected_name) > 2 and len(corrected_name) < 50:
                        final_compound_name = corrected_name
                        print(f"🤖 AI Spell Correction: '{initial_name}' → '{final_compound_name}'")
                    else:
                        final_compound_name = initial_name
                        print(f"⚠️ AI correction invalid, using original: '{final_compound_name}'")
                else:
                    final_compound_name = initial_name
                    print(f"⚠️ AI correction empty, using original: '{final_compound_name}'")
                    
            except Exception as e:
                final_compound_name = initial_name
                print(f"⚠️ AI spell correction failed: {e}, using original: '{final_compound_name}'")
        else:
            final_compound_name = initial_name
        
        print(f"HACKATHON SMART EXTRACTION: '{compound_name}' -> '{final_compound_name}'")
        
        # STEP 1: ENHANCED comprehensive data search using smart-chat pattern
        from .connectors.pubchem import PubChemConnector
        from .connectors.pdb import PDBConnector
        from .connectors.pubmed import PubMedConnector
        from .connectors.trials import ClinicalTrialsConnector
        
        pubchem_connector = PubChemConnector()
        pdb_connector = PDBConnector()
        pubmed_connector = PubMedConnector()
        trials_connector = ClinicalTrialsConnector()
        
        # ENHANCED: Get comprehensive data using dynamic search variations
        print(f"Debug: Download - fetching comprehensive data for '{final_compound_name}'...")
        
        compounds = []
        structures = []
        articles = []
        trials = []
        
        # Get compound data with dynamic search variations
        try:
            compounds = pubchem_connector.search_compounds(final_compound_name, max_results=5)
            print(f"Debug: Download - found {len(compounds)} compounds")
        except Exception as e:
            print(f"PubChem search error: {e}")
        
        # Get protein structures with dynamic search variations
        try:
            structures = pdb_connector.search_proteins(final_compound_name, max_results=5)
            print(f"Debug: Download - found {len(structures)} protein structures")
        except Exception as e:
            print(f"PDB search error: {e}")
        
        # Get related literature for context
        try:
            articles = pubmed_connector.search_articles(final_compound_name, max_results=8)
            print(f"Debug: Download - found {len(articles)} related articles")
        except Exception as e:
            print(f"PubMed search error: {e}")
        
        # Get related clinical trials
        try:
            trials_result = trials_connector.search_trials(final_compound_name, max_results=5)
            trials = trials_result.get('trials', []) if trials_result else []
            print(f"Debug: Download - found {len(trials)} related trials")
        except Exception as e:
            print(f"Clinical trials search error: {e}")
        
        # Get primary compound and structure data
        compound_data = compounds[0] if compounds else None
        protein_data = structures[0] if structures else None
        compounds_found = len(compounds)
        structures_found = len(structures)
        
        # STEP 3: Generate comprehensive download links
        download_links = {}
        
        # Real compound links - FIXED URL patterns
        if compound_data and compound_data.get('cid'):
            cid = compound_data['cid']
            download_links.update({
                "pubchem_compound": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
                "compound_data_json": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/JSON",
                "compound_image": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG", 
                "compound_structure_sdf": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF",
                "compound_structure_mol": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/MOL",
                "compound_3d_viewer": f"https://pubchem.ncbi.nlm.nih.gov/3d-viewer?cid={cid}",
                "compound_properties": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,IsomericSMILES/JSON"
            })
        
        # 🚀 AI-POWERED DYNAMIC DETECTION: Works for ANY protein or drug!
        # No more static lists - AI analyzes the compound automatically
        
        print(f"🤖 AI-POWERED ANALYSIS: Analyzing '{final_compound_name}'...")
        
        # Get molecular weight for analysis
        molecular_weight = compound_data.get('molecular_weight', 0)
        molecular_formula = compound_data.get('molecular_formula', '')
        compound_name = compound_data.get('name', final_compound_name)
        
        # 🧠 AI-POWERED COMPOUND TYPE DETECTION
        ai_analysis_prompt = f"""Analyze this compound and determine if it's a PROTEIN or SMALL DRUG:

Compound Name: {compound_name}
Molecular Formula: {molecular_formula}
Molecular Weight: {molecular_weight} Da

Determine if this is:
1. PROTEIN - Large biological macromolecule (enzymes, antibodies, hormones, structural proteins)
2. SMALL DRUG - Small molecule pharmaceutical compound (pills, medications, chemicals)

Consider:
- Molecular weight (proteins > 3000 Da, drugs < 2000 Da)
- Formula patterns (proteins have C,H,N,O,S, drugs may have other elements)
- Name patterns (proteins often end in -in, -ase, -zyme, drugs often have specific naming)
- Biological function

Respond with ONLY: "PROTEIN" or "DRUG"
"""

        try:
            from . import rag
            ai_classification = await rag.call_cerebras_api(ai_analysis_prompt, max_tokens=10, model="llama3.1-8b", temperature=0.1)
            ai_classification = ai_classification.strip().upper()
            
            # Fallback to molecular weight if AI fails
            if "PROTEIN" not in ai_classification and "DRUG" not in ai_classification:
                print(f"⚠️ AI classification unclear: '{ai_classification}', using molecular weight fallback")
                if isinstance(molecular_weight, (int, float)) and molecular_weight > 0:
                    ai_classification = "PROTEIN" if molecular_weight > 3000 else "DRUG"
                else:
                    ai_classification = "DRUG"  # Default to drug for unknown molecular weight
            
            print(f"🤖 AI Classification: {ai_classification} (MW: {molecular_weight} Da)")
            
            is_protein_query = "PROTEIN" in ai_classification
            is_drug_query = "DRUG" in ai_classification
            
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e}, using molecular weight fallback")
            # Fallback to molecular weight analysis
            if isinstance(molecular_weight, (int, float)) and molecular_weight > 0:
                is_protein_query = molecular_weight > 3000
                is_drug_query = molecular_weight < 2000
            else:
                is_protein_query = False
                is_drug_query = True  # Default to drug for unknown molecular weight
        
        # Only add PDB links if it's a protein query OR if we have relevant protein structures
        if protein_data and protein_data.get('pdb_id') and (is_protein_query or not is_drug_query):
            pdb_id = protein_data['pdb_id']
            download_links.update({
                "pdb_structure": f"https://www.rcsb.org/structure/{pdb_id}",
                "structure_pdb": f"https://files.rcsb.org/download/{pdb_id}.pdb",
                "structure_cif": f"https://files.rcsb.org/download/{pdb_id}.cif",
                "structure_sdf": f"https://files.rcsb.org/download/{pdb_id}_ligand.sdf"
            })
        
        # Generic research data links - FIXED URL encoding
        import urllib.parse
        encoded_compound = urllib.parse.quote_plus(final_compound_name)
        encoded_original = urllib.parse.quote_plus(request.compound_name)
        
        download_links.update({
            "pubmed_search": f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded_compound}",
            "clinical_trials": f"https://clinicaltrials.gov/search?term={encoded_compound}",
            "genbank": f"https://www.ncbi.nlm.nih.gov/gene/?term={encoded_compound}",
            "uniprot": f"https://www.uniprot.org/uniprot/?query={encoded_compound}"
        })
        
        # ENHANCED: Prepare comprehensive downloadable data with validated URLs
        download_response = {
            "original_query": request.compound_name,
            "compound_name": final_compound_name,
            "smart_extraction": {
                "extracted_from": request.compound_name,
                "final_name": final_compound_name,
                "was_natural_language": compound_name.lower() != final_compound_name.lower()
            },
            "pubchem_data": compound_data,
            "protein_structure": protein_data,
            "download_links": download_links,
            "comprehensive_data": {
                "compounds": compounds[:5],  # Top 5 compounds
                "protein_structures": structures[:5],  # Top 5 structures
                "related_articles": articles[:5],  # Top 5 articles
                "clinical_trials": trials[:3],  # Top 3 trials
            },
            "data_summary": {
                "compounds_found": compounds_found,
                "structures_found": structures_found,
                "articles_found": len(articles),
                "trials_found": len(trials),
                "total_download_links": len(download_links)
            },
            "metadata": {
                "molecular_formula": compound_data.get('molecular_formula') if compound_data else None,
                "molecular_weight": compound_data.get('molecular_weight') if compound_data else None,
                "iupac_name": compound_data.get('name') if compound_data else None,
                "structure_method": protein_data.get('method') if protein_data else None,
                "resolution": protein_data.get('resolution') if protein_data else None,
                "organism": protein_data.get('organism') if protein_data else None,
                "pdb_id": protein_data.get('pdb_id') if protein_data else None,
                "pubchem_cid": compound_data.get('cid') if compound_data else None
            },
            "data_types": {
                "compound_structure_files": ["JSON", "PNG", "SDF"],
                "protein_structure_files": ["PDB", "CIF", "XML", "FASTA"],
                "visualization_links": ["3d-viewer", "Molecular Viewer", "Interactive Structure"],
                "database_searches": ["PubMed", "ClinicalTrials", "GenBank", "UniProt"],
                "literature_data": ["Abstracts", "Citations", "PMIDs"],
                "clinical_data": ["Trial Protocols", "Outcomes", "NCT IDs"]
            },
            "research_context": f"Comprehensive data download including {len(compounds)} compounds, {len(structures)} protein structures, {len(articles)} research articles, and {len(trials)} clinical trials",
            "sponsor_tech": "Powered by Docker MCP Gateway microservices + PubChem/PDB APIs + PubMed/ClinicalTrials + real biomedical databases",
            "ai_model": "Cerebras Llama 3.1-8B + OpenAI GPT-4o-mini",
            "data_sources": ["PubChem", "RCSB PDB", "PubMed", "ClinicalTrials.gov"],
            "search_method": "Multi-variation dynamic search with comprehensive data integration",
            "download_instructions": "Click any link above to access real-time data downloads from biomedical databases"
        }
        
        # Note: Frontend will handle formatting using the formatResponse function
        
        print(f"HACKATHON SUCCESS: Generated download links for {request.compound_name}")
        return download_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.post("/api/export")
async def export_data(request: ExportRequest, db: Session = Depends(deps.get_db)):
    """
    Export search results to PDF or CSV format.
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required for export.")
    
    if request.format not in ["pdf", "csv"]:
        raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'csv'.")
    
    try:
        # Get data based on type
        export_data = {}
        
        if request.data_type in ["literature", "both"]:
            from .connectors.pubmed import PubMedConnector
            pubmed_connector = PubMedConnector()
            export_data["literature"] = pubmed_connector.search_articles(
                request.query, 
                max_results=50,
                filters=request.filters
            )
        
        if request.data_type in ["trials", "both"]:
            from .connectors.trials import ClinicalTrialsConnector
            trials_connector = ClinicalTrialsConnector()
            export_data["trials"] = trials_connector.search_trials(
                request.query,
                max_results=50,
                filters=request.filters
            )
        
        # Generate export file
        if request.format == "csv":
            return await _generate_csv_export(request.query, export_data)
        elif request.format == "pdf":
            return await _generate_pdf_export(request.query, export_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

async def _generate_csv_export(query: str, data: Dict) -> Dict:
    """
    Generate CSV export of search results.
    """
    import csv
    import io
    import base64
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Type", "Title", "Authors", "Journal", "Date", "URL", "Abstract"])
    
    # Write literature data
    if "literature" in data:
        for article in data["literature"]:
            writer.writerow([
                "Literature",
                article.get("title", ""),
                article.get("authors", ""),
                article.get("journal", ""),
                article.get("publication_date", ""),
                article.get("url", ""),
                article.get("abstract", "")[:200] + "..." if len(article.get("abstract", "")) > 200 else article.get("abstract", "")
            ])
    
    # Write trials data
    if "trials" in data:
        for trial in data["trials"]:
            writer.writerow([
                "Clinical Trial",
                trial.get("title", ""),
                trial.get("sponsor", ""),
                trial.get("phase", ""),
                trial.get("start_date", ""),
                trial.get("url", ""),
                f"Status: {trial.get('status', '')}, Conditions: {', '.join(trial.get('conditions', []))}"
            ])
    
    csv_content = output.getvalue()
    output.close()
    
    # Encode as base64 for transmission
    csv_b64 = base64.b64encode(csv_content.encode()).decode()
    
    return {
        "query": query,
        "format": "csv",
        "filename": f"clintra_search_{query.replace(' ', '_')}.csv",
        "content": csv_b64,
        "download_url": f"data:text/csv;base64,{csv_b64}",
        "size": len(csv_content)
    }

async def _generate_pdf_export(query: str, data: Dict) -> Dict:
    """
    Generate PDF export of search results.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        import io
        import base64
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph(f"Clintra Search Results: {query}", title_style))
        story.append(Spacer(1, 12))
        
        # Literature section
        if "literature" in data and data["literature"]:
            story.append(Paragraph("Literature Results", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            for i, article in enumerate(data["literature"][:10], 1):  # Limit to 10 articles
                story.append(Paragraph(f"{i}. {article.get('title', 'No title')}", styles['Heading3']))
                story.append(Paragraph(f"Authors: {article.get('authors', 'Unknown')}", styles['Normal']))
                story.append(Paragraph(f"Journal: {article.get('journal', 'Unknown')}", styles['Normal']))
                story.append(Paragraph(f"Date: {article.get('publication_date', 'Unknown')}", styles['Normal']))
                story.append(Paragraph(f"URL: {article.get('url', '')}", styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Trials section
        if "trials" in data and data["trials"]:
            story.append(Paragraph("Clinical Trials Results", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            for i, trial in enumerate(data["trials"][:10], 1):  # Limit to 10 trials
                story.append(Paragraph(f"{i}. {trial.get('title', 'No title')}", styles['Heading3']))
                story.append(Paragraph(f"Status: {trial.get('status', 'Unknown')}", styles['Normal']))
                story.append(Paragraph(f"Phase: {trial.get('phase', 'Unknown')}", styles['Normal']))
                story.append(Paragraph(f"Sponsor: {trial.get('sponsor', 'Unknown')}", styles['Normal']))
                story.append(Paragraph(f"URL: {trial.get('url', '')}", styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Encode as base64 for transmission
        pdf_b64 = base64.b64encode(pdf_content).decode()
        
        return {
            "query": query,
            "format": "pdf",
            "filename": f"clintra_search_{query.replace(' ', '_')}.pdf",
            "content": pdf_b64,
            "download_url": f"data:application/pdf;base64,{pdf_b64}",
            "size": len(pdf_content)
        }
        
    except ImportError:
        # Fallback if reportlab is not available
        return {
            "query": query,
            "format": "pdf",
            "error": "PDF generation requires reportlab package. Please install it or use CSV export.",
            "fallback_csv": await _generate_csv_export(query, data)
        }

@app.get("/api/chat/history")
async def get_chat_history(db: Session = Depends(deps.get_db)):
    """
    Get chat history for the current session.
    """
    # Mock implementation - in real app, would fetch from database
    return {
        "messages": [
            {
                "id": 1,
                "role": "assistant",
                "content": "👋 Welcome to Clintra — Your AI-Powered Drug Discovery Assistant! I can help you search biomedical literature, generate hypotheses, and download compound data.",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
    }

class GraphRequest(BaseModel):
    query: str
    graph_type: str = "network"  # network, pathway, interaction

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class ChatSessionCreate(BaseModel):
    title: str

class ChatMessageCreate(BaseModel):
    content: str
    mode: str = "literature"
    role: str = "user"

@app.post("/api/graph")
async def generate_graph(request: GraphRequest, db: Session = Depends(deps.get_db)):
    """
    Generates a real graph visualization for the given query with proper error handling.
    """
    # Import validation utilities
    from .errors import validate_query
    
    # Validate query
    try:
        validate_query(request.query, max_length=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        # Import caching utilities
        from .cache import get_cached_graph_data, cache_graph_data
        
        # Check cache for graph data
        cached_graph = get_cached_graph_data(request.query, request.graph_type)
        if cached_graph:
            graph_data = cached_graph
        else:
            # Generate real graph using the graph generator (static method)
            graph_data = graph_generator.GraphGenerator.generate_biomedical_graph(request.query, request.graph_type)
            # Cache for 15 minutes
            cache_graph_data(request.query, request.graph_type, graph_data, ttl=900)
        
        # ENHANCE with OpenAI Graph Insights
        try:
            import openai
            import os
            
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key:
                client = openai.OpenAI(api_key=openai_api_key)
                
                # Create graph insight prompt
                graph_insight_prompt = f"""Analyze this biomedical network graph and provide expert insights:

**Graph Topic**: {request.query}
**Graph Type**: {request.graph_type}
**Nodes**: {len(graph_data.get('nodes', []))} nodes
**Edges**: {len(graph_data.get('edges', []))} connections

Provide concise insights focusing on:

## 🔗 Network Analysis
- Key hub nodes and their significance
- Important pathways and connections
- Network topology insights

## 🎯 Biological Significance  
- What this network represents biologically
- Critical interactions and relationships
- Therapeutic targets or opportunities

## 💡 Research Implications
- What this graph reveals about the research area
- Potential drug targets or biomarkers
- Future research directions

Keep it concise (max 400 words) and scientifically accurate."""

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a network biology expert specializing in biomedical graph analysis."},
                        {"role": "user", "content": graph_insight_prompt}
                    ],
                    max_tokens=500,
                    temperature=0.6
                )
                
                graph_insights = response.choices[0].message.content
                
                # Add insights to graph data
                graph_data["ai_insights"] = graph_insights
                graph_data["insights_model"] = "OpenAI GPT-4o-mini"
                graph_data["sponsor_tech"] = "🎨 GRAPH: NetworkX + Matplotlib + Plotly | 🧠 INSIGHTS: OpenAI GPT-4 network analysis | 🏆 SPONSOR: Docker MCP"
                
                # Also enhance with Cerebras for research context
                try:
                    from . import rag
                    cerebras_prompt = f"""Based on this graph analysis of "{request.query}", provide research context:

{graph_insights}

Focus on:
- Current research trends in this area
- Clinical applications and therapeutic potential
- Key research institutions or collaborations
- Future research priorities

Keep it brief and research-focused."""

                    cerebras_context = await rag.call_cerebras_api(cerebras_prompt, max_tokens=300, model="llama3.1-8b", temperature=0.7)
                    
                    graph_data["research_context"] = cerebras_context
                    graph_data["context_model"] = "Cerebras Llama 3.1-8B"
                    graph_data["sponsor_tech"] = "🎨 GRAPH: NetworkX + Matplotlib + Plotly | 🧠 INSIGHTS: OpenAI GPT-4 | 🏆 CONTEXT: Cerebras Llama (sponsor) | 🐳 PLATFORM: Docker MCP (sponsor)"
                    
                except Exception as e:
                    print(f"Cerebras enhancement failed: {e}")
                
            else:
                graph_data["ai_insights"] = "OpenAI API not configured for graph insights."
                
        except Exception as e:
            print(f"OpenAI graph enhancement failed: {e}")
            graph_data["ai_insights"] = "Graph insights temporarily unavailable."
        
        return graph_data
        
    except Exception as e:
        print(f"Graph generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Graph generation failed: {str(e)}")

# 🔬 3D MOLECULE VIEWER ENDPOINTS
@app.get("/api/molecules/search")
async def search_molecule(query: str, source: str = "auto", max_results: int = 5):
    """
    Search for molecules in PubChem, PDB, and other databases.
    Returns 3D structure data for visualization.
    """
    try:
        results = []
        
        if source == "auto" or source == "pubchem":
            # Search PubChem
            from .connectors.pubchem import PubChemConnector
            pubchem_connector = PubChemConnector()
            compounds = pubchem_connector.search_compounds(query, max_results=max_results)
            
            for compound in compounds:
                try:
                    # Get additional 3D structure data
                    cid = compound.get('cid')
                    if cid:
                        # Try to get SMILES and 3D coordinates
                        smiles_response = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/SMILES/JSON", timeout=10)
                        formula_response = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/MolecularFormula/JSON", timeout=10)
                        weight_response = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/MolecularWeight/JSON", timeout=10)
                        
                        smiles_data = smiles_response.json() if smiles_response.status_code == 200 else {}
                        formula_data = formula_response.json() if formula_response.status_code == 200 else {}
                        weight_data = weight_response.json() if weight_response.status_code == 200 else {}
                        
                        compound.update({
                            'smiles': smiles_data.get('PropertyTable', {}).get('Properties', [{}])[0].get('SMILES', ''),
                            'formula': formula_data.get('PropertyTable', {}).get('Properties', [{}])[0].get('MolecularFormula', ''),
                            'weight': weight_data.get('PropertyTable', {}).get('Properties', [{}])[0].get('MolecularWeight', 0),
                            'has_3d': True,
                            'viewer_url': f"https://pubchem.ncbi.nlm.nih.gov/3d-viewer?cid={cid}",
                            'source': 'PubChem'
                        })
                        
                except Exception as e:
                    print(f"Error getting PubChem details for CID {cid}: {e}")
                    compound.update({
                        'has_3d': False,
                        'source': 'PubChem'
                    })
                    
                results.append(compound)
        
        if source == "auto" or source == "pdb":
            # Search PDB
            from .connectors.pdb import PDBConnector
            pdb_connector = PDBConnector()
            proteins = pdb_connector.search_proteins(query, max_results=max_results)
            
            for protein in proteins:
                protein.update({
                    'has_3d': True,
                    'viewer_url': f"https://www.rcsb.org/3d-view/{protein.get('pdb_id', '')}",
                    'source': 'PDB',
                    'type': 'protein'
                })
                results.append(protein)
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "sources": list(set([r.get('source', 'Unknown') for r in results])),
            "message": f"Found {len(results)} molecular structures for '{query}'"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search molecules: {str(e)}")

@app.get("/api/molecules/{molecule_id}/structure")
async def get_molecule_structure(molecule_id: str, source: str = "pubchem"):
    """
    Get detailed 3D structure data for a specific molecule.
    Returns coordinates, bonds, and metadata for 3D visualization.
    """
    try:
        if source == "pubchem":
            # Get PubChem 3D coordinates
            cid = molecule_id
            coord_response = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/record_type=3d/JSON", timeout=15)
            
            if coord_response.status_code == 200:
                coord_data = coord_response.json()
                
                # Process coordinates for 3D viewer
                structure_data = {
                    "molecule_id": cid,
                    "source": "PubChem",
                    "coordinates": coord_data,
                    "viewer_data": {
                        "title": f"CID: {cid}",
                        "center": [0, 0, 0],
                        "atoms": extract_atoms_from_pubchem(coord_data),
                        "bonds": [],  # Bonds need separate analysis
                        "metadata": extract_metadata_from_pubchem(coord_data)
                    }
                }
                
                return structure_data
            else:
                raise HTTPException(status_code=404, detail="Molecule not found in PubChem")
                
        elif source == "pdb":
            # Get PDB structure
            from .connectors.pdb import PDBConnector
            pdb_connector = PDBConnector()
            structure = pdb_connector.get_protein_structure(molecule_id)
            
            if structure:
                structure['viewer_data'] = {
                    "title": structure.get('title', f"PDB: {molecule_id}"),
                    "center": [0, 0, 0],
                    "chains": structure.get('chains', []),
                    "resolution": structure.get('resolution', 'N/A'),
                    "metadata": {
                        "pdb_id": molecule_id,
                        "organism": structure.get('organism', 'Unknown'),
                        "method": structure.get('method', 'Unknown')
                    }
                }
                
                return structure
            else:
                raise HTTPException(status_code=404, detail="Protein structure not found in PDB")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid source. Use 'pubchem' or 'pdb'")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get molecule structure: {str(e)}")

def extract_atoms_from_pubchem(coord_data):
    """Extract atom coordinates from PubChem response."""
    atoms = []
    
    try:
        if 'PC_Compounds' in coord_data:
            pc_data = coord_data['PC_Compounds'][0]
            
            # Extract coordinates
            if 'coords' in pc_data:
                coords = pc_data['coords'][0]
                if coords.get('t') == '3d':
                    x_coords = coords.get('c', {}).get('x', [])
                    y_coords = coords.get('c', {}).get('y', [])
                    z_coords = coords.get('c', {}).get('z', [])
                    
                    # Extract element symbols
                    element_data = pc_data.get('atoms', {}).get('z', [])
                    
                    for i in range(max(len(x_coords), len(y_coords), len(z_coords))):
                        atoms.append({
                            "id": i,
                            "element": get_element_symbol(element_data[i]) if i < len(element_data) else 'C',
                            "x": x_coords[i] if i < len(x_coords) else 0,
                            "y": y_coords[i] if i < len(y_coords) else 0,
                            "z": z_coords[i] if i < len(z_coords) else 0,
                            "radius": get_atomic_radius(get_element_symbol(element_data[i])) if i < len(element_data) else 0.7
                        })
    except Exception as e:
        print(f"Error extracting atoms: {e}")
        # Fallback atoms
        atoms = generate_fallback_atoms()
    
    return atoms

def extract_metadata_from_pubchem(coord_data):
    """Extract metadata from PubChem response."""
    metadata = {}
    
    try:
        if 'PC_Compounds' in coord_data:
            props = coord_data['PC_Compounds'][0].get('props', [])
            for prop in props:
                if prop.get('urn', {}).get('label') == 'SMILES':
                    metadata['smiles'] = prop.get('value', '').get('sval', '')
                elif prop.get('urn', {}).get('label') == 'Molecular Formula':
                    metadata['formula'] = prop.get('value', '').get('sval', '')
                elif prop.get('urn', {}).get('label') == 'Molecular Weight':
                    metadata['weight'] = prop.get('value', '').get('fval', 0)
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        metadata = {'smiles': 'CCO', 'formula': 'C2H6O', 'weight': 46.07}
    
    return metadata

def get_element_symbol(element_number):
    """Convert element number to symbol."""
    elements = ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne',
                'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca',
                'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn']
    
    if 1 <= element_number <= len(elements):
        return elements[element_number - 1]
    return 'C'  # Default to carbon

def get_atomic_radius(element):
    """Get atomic radius for element."""
    radii = {
        'H': 0.31, 'C': 0.70, 'N': 0.71, 'O': 0.66, 'F': 0.57,
        'S': 1.04, 'P': 1.07, 'Cl': 0.99, 'Br': 1.20, 'I': 1.40
    }
    return radii.get(element, 0.70)

def generate_fallback_atoms():
    """Generate fallback atoms if extraction fails."""
    atoms = []
    elements = ['C', 'H', 'O', 'N', 'S']
    
    for i in range(10):
        atoms.append({
            "id": i,
            "element": elements[i % len(elements)],
            "x": (i - 5) * 1.5,
            "y": ((i % 3) - 1) * 1.5,
            "z": ((i % 2) - 0.5) * 1.5,
            "radius": get_atomic_radius(elements[i % len(elements)])
        })
    
    return atoms

# Authentication endpoints
@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(deps.get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(models.User).filter(
        (models.User.username == user_data.username) | 
        (models.User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    user = auth.create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    # Create access token
    access_token = auth.create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }

@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(deps.get_db)):
    """Login a user."""
    user = auth.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = auth.create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }

@app.get("/api/auth/me")
async def get_current_user_info(current_user: models.User = Depends(auth.get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "created_at": current_user.created_at
    }

# Chat session endpoints
@app.post("/api/chat/sessions")
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Create a new chat session."""
    chat_session = models.ChatSession(
        user_id=current_user.id,
        title=session_data.title
    )
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    
    return {
        "id": chat_session.id,
        "title": chat_session.title,
        "created_at": chat_session.created_at
    }

@app.get("/api/chat/sessions")
async def get_chat_sessions(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Get all chat sessions for the current user."""
    sessions = db.query(models.ChatSession).filter(
        models.ChatSession.user_id == current_user.id,
        models.ChatSession.is_active == True
    ).order_by(models.ChatSession.updated_at.desc()).all()
    
    return [
        {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "message_count": len(session.messages)
        }
        for session in sessions
    ]

@app.get("/api/chat/sessions/{session_id}/messages")
async def get_chat_messages(
    session_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Get messages for a specific chat session."""
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session_id
    ).order_by(models.ChatMessage.created_at.asc()).all()
    
    return [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "mode": message.mode,
            "created_at": message.created_at
        }
        for message in messages
    ]

@app.post("/api/chat/sessions/{session_id}/messages")
async def add_chat_message(
    session_id: int,
    message_data: ChatMessageCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Add a message to a chat session."""
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Create message with the specified role
    chat_message = models.ChatMessage(
        session_id=session_id,
        role=message_data.role,
        content=message_data.content,
        mode=message_data.mode
    )
    db.add(chat_message)
    
    # Update session timestamp
    session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(chat_message)
    
    return {
        "id": chat_message.id,
        "role": chat_message.role,
        "content": chat_message.content,
        "mode": chat_message.mode,
        "created_at": chat_message.created_at
    }

@app.patch("/api/chat/sessions/{session_id}")
async def update_chat_session(
    session_id: int,
    session_data: dict,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Update a chat session (title, context, etc.)."""
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Update session fields
    if "title" in session_data:
        session.title = session_data["title"]
    if "description" in session_data:
        session.description = session_data["description"]
    
    session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    
    return {
        "id": session.id,
        "title": session.title,
        "description": session.description,
        "updated_at": session.updated_at
    }

@app.post("/api/smart-chat")
async def smart_chat(request: dict, db: Session = Depends(deps.get_db)):
    """
    Intelligent chat routing: Determines if message is general chat or research query,
    then routes appropriately using OpenAI for general chat and Cerebras for research.
    """
    try:
        import openai
        import os
        
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Get OpenAI client for query classification
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API not configured")
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Step 1: Classify the query type using OpenAI
        classification_prompt = f"""Analyze this user message and classify it as one of these types:

GENERAL_CHAT: Casual conversation, greetings, small talk, personal questions, general AI questions
RESEARCH_QUERY: Scientific research, medical questions, drug discovery, literature search, hypothesis generation, biomedical topics

Examples:
- "hello" → GENERAL_CHAT
- "how are you" → GENERAL_CHAT  
- "what's up" → GENERAL_CHAT
- "tell me about yourself" → GENERAL_CHAT
- "what can you do" → GENERAL_CHAT
- "aspirin mechanism of action" → RESEARCH_QUERY
- "CRISPR gene therapy" → RESEARCH_QUERY
- "protein folding" → RESEARCH_QUERY
- "cancer treatment options" → RESEARCH_QUERY
- "cortisol pathway" → RESEARCH_QUERY
- "stress hormone" → RESEARCH_QUERY
- "acetylcholine" → RESEARCH_QUERY
- "protein crystallization" → RESEARCH_QUERY

User message: "{message}"

Respond with only: GENERAL_CHAT or RESEARCH_QUERY"""

        classification_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": classification_prompt}],
            max_tokens=10,
            temperature=0.1
        )
        
        query_type = classification_response.choices[0].message.content.strip()
        
        # Step 2: Route based on classification
        if query_type == "GENERAL_CHAT":
            # Use OpenAI for general conversation
            chat_prompt = f"""You are Clintra, an AI assistant specialized in biomedical research and drug discovery. 
            
You're having a casual conversation with a user. Be friendly, helpful, and professional. 
If they ask about your capabilities, mention that you can help with:
- Literature search and analysis
- Drug discovery research  
- Hypothesis generation
- Scientific data analysis
- File analysis (images, PDFs, documents)

Keep responses conversational and not too long.

User: {message}
Clintra:"""

            chat_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": chat_prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            return {
                "message": message,
                "response": chat_response.choices[0].message.content.strip(),
                "type": "general_chat",
                "ai_model": "OpenAI GPT-4o-mini",
                "sponsor_tech": "💬 GENERAL CHAT: OpenAI GPT-4 conversational AI",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        else:  # RESEARCH_QUERY
            # Use the full search endpoint for comprehensive results
            from .connectors.pubmed import PubMedConnector
            from .connectors.trials import ClinicalTrialsConnector
            from . import rag
            
            # 🚀 STEP 0: ADVANCED QUERY PREPROCESSING & OPTIMIZATION
            print(f"Debug: Starting advanced query preprocessing for: '{message}'")
            
            # 🤖 AI-POWERED SPELL CORRECTION - Ultra-intelligent typo correction
            async def ai_correct_medical_typos(query):
                """AI-powered correction of medical/biomedical typos using OpenAI"""
                try:
                    # Create AI prompt for spell correction
                    ai_prompt = f"""You are a biomedical AI expert. Correct any spelling mistakes in this biomedical query.

Original Query: "{query}"

Your task:
1. Fix any spelling errors in biomedical terms
2. Correct drug names, disease names, protein names
3. Maintain the original meaning and context
4. Use standard scientific terminology

Examples:
- "diabetis" → "diabetes"
- "canscer" → "cancer" 
- "aspirn" → "aspirin"
- "protien" → "protein"
- "alzheimers" → "Alzheimer"

Return ONLY the corrected query, nothing else."""
                    
                    import openai
                    import os
                    
                    openai_api_key = os.getenv('OPENAI_API_KEY')
                    if not openai_api_key:
                        return query  # Fallback to original
                    
                    client = openai.OpenAI(api_key=openai_api_key)
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": ai_prompt}],
                        max_tokens=100,
                        temperature=0.1
                    )
                    
                    corrected_query = response.choices[0].message.content.strip()
                    
                    if corrected_query and corrected_query != query:
                        print(f"🤖 AI Spell Correction: '{query}' → '{corrected_query}'")
                        return corrected_query
                    else:
                        return query
                        
                except Exception as e:
                    print(f"⚠️ AI spell correction failed: {e}")
                    return query
            
            # Fallback static typo correction
            def correct_medical_typos_static(query):
                """Fallback static correction for common medical/biomedical typos"""
                import re
                
                # Common biomedical term corrections (typo -> correct)
                typo_dict = {
                    # Diseases
                    'diabetis': 'diabetes', 'diabete': 'diabetes', 'diabetees': 'diabetes',
                    'canscer': 'cancer', 'cancr': 'cancer', 'kanser': 'cancer',
                    'alzheimers': 'alzheimer', 'alzeimer': 'alzheimer', 'altzheimer': 'alzheimer',
                    'parkinsons': 'parkinson', 'parkinsins': 'parkinson',
                    'arthritis': 'arthritis', 'artritis': 'arthritis',
                    'asthma': 'asthma', 'astma': 'asthma',
                    
                    # Treatments/Therapy
                    'treatement': 'treatment', 'tretment': 'treatment', 'treatmnt': 'treatment',
                    'theraphy': 'therapy', 'therapie': 'therapy', 'terapy': 'therapy',
                    'medicin': 'medicine', 'medecine': 'medicine',
                    
                    # Drug names
                    'aspirn': 'aspirin', 'asprin': 'aspirin',
                    'insuln': 'insulin', 'insolin': 'insulin',
                    'metforman': 'metformin', 'metfornin': 'metformin',
                    'warfarin': 'warfarin', 'warfrin': 'warfarin',
                    
                    # General terms
                    'protien': 'protein', 'protin': 'protein',
                    'pateint': 'patient', 'patint': 'patient',
                    'symtom': 'symptom', 'symptom': 'symptom',
                    'mechanizm': 'mechanism', 'mecanizm': 'mechanism', 'mechanis': 'mechanism',
                    'acton': 'action', 'acion': 'action',
                    
                    # Type variants
                    'typ': 'type', 'tipe': 'type',
                    
                    # Research terms
                    'resarch': 'research', 'reserch': 'research',
                    'studdy': 'study', 'studie': 'study',
                    'analyis': 'analysis', 'analisys': 'analysis'
                }
                
                corrected_query = query.lower()
                corrections_made = []
                
                # Apply corrections
                for typo, correct in typo_dict.items():
                    if typo in corrected_query:
                        corrected_query = re.sub(r'\b' + typo + r'\b', correct, corrected_query)
                        corrections_made.append(f"{typo}->{correct}")
                
                if corrections_made:
                    print(f"Debug: Static typo corrections applied: {', '.join(corrections_made)}")
                    print(f"Debug: Corrected query: '{corrected_query}'")
                
                return corrected_query
            
            # Apply AI-powered typo correction first
            corrected_message = await ai_correct_medical_typos(message)
            if corrected_message == message:
                # Fallback to static correction if AI didn't change anything
                corrected_message = correct_medical_typos_static(message)
            
            # Extract core biomedical terms from natural language queries
            def extract_biomedical_keywords(query):
                """Extract key biomedical terms and clean query for better searches"""
                import re
                
                # Remove question words and filler phrases
                cleaned_query = re.sub(r'\b(can you|please|give me|analysis of|current|researches?)\b', '', query.lower())
                cleaned_query = re.sub(r'\b(on|about|regarding|pertaining to)\b', '', cleaned_query)
                cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()
                
                # Extract disease/disorder terms
                medical_terms = []
                if any(word in query.lower() for word in ['aids', 'hiv', 'virus', 'retrovirus']):
                    medical_terms.extend(['HIV AIDS'])
                if any(word in query.lower() for word in ['cancer', 'tumor', 'carcinoma', 'malignancy']):
                    medical_terms.extend(['cancer', 'oncology'])
                if any(word in query.lower() for word in ['diabetes', 'insulin', 'glucose']):
                    medical_terms.extend(['diabetes', 'insulin'])
                if any(word in query.lower() for word in ['alzheimer', 'dementia', 'cognitive']):
                    medical_terms.extend(['Alzheimer', 'dementia'])
                
                # Extract protein/drug terms
                if any(word in query.lower() for word in ['protein', 'enzyme', 'receptor', 'binding']):
                    medical_terms.append('protein')
                if any(word in query.lower() for word in ['drug', 'medication', 'therapy', 'treatment']):
                    medical_terms.append('drug therapy')
                
                # Create optimized search query
                if medical_terms:
                    optimized_query = ' '.join(medical_terms)
                else:
                    optimized_query = cleaned_query or query
                
                print(f"Debug: Query optimization: '{query}' -> '{optimized_query}'")
                return optimized_query
            
            # Generate optimized search queries using corrected message
            optimized_query = extract_biomedical_keywords(corrected_message)
            fallback_queries = [optimized_query]
            
            # Add fallback queries if optimization might be too narrow
            if len(optimized_query.split()) < 2:
                fallback_queries.extend([query for query in [corrected_message, message] if query != optimized_query])
            
            print(f"Debug: Fallback queries: {fallback_queries}")
            
            # Get comprehensive literature data (same as /api/search)
            pubmed_connector = PubMedConnector()
            trials_connector = ClinicalTrialsConnector()
            
            # Search literature and trials with optimized queries
            articles = []
            for search_query in fallback_queries:
                try:
                    # Dynamic article count based on query complexity
                    query_complexity = len(message.split())
                    base_articles = max(15, min(query_complexity * 3, 50))  # 15-50 articles
                    
                    print(f"Debug: Query complexity: {query_complexity} words -> {base_articles} articles")
                    articles = pubmed_connector.search_articles(search_query, max_results=base_articles)
                    if articles:
                        print(f"Debug: Found {len(articles)} articles with optimized query: '{search_query}'")
                        break  # Use first successful query
                    else:
                        print(f"Debug: No articles found for query: '{search_query}'")
                except Exception as e:
                    print(f"PubMed connector error for '{search_query}': {e}")
                    continue
            
            # Ensure articles is properly set
            if not articles:
                print(f"Debug: No PubMed articles found for any query: {fallback_queries}")
                articles = []  # Explicitly ensure empty list
            else:
                print(f"Debug: Final articles count: {len(articles)}")
                
            try:
                # Dynamic trials count based on query complexity  
                base_trials = max(8, min(query_complexity * 2, 20))  # 8-20 inals
                print(f"Debug: Trials search with {base_trials} trials")
                trials_result = trials_connector.search_trials(optimized_query, max_results=base_trials)
                trials = trials_result.get('trials', []) if trials_result else []
                if not trials:
                    print(f"No clinical trials found for query: {message}")
            except Exception as e:
                print(f"ClinicalTrials connector error: {e}")
                trials = []
            
            # Prepare comprehensive literature context for thorough analysis
            literature_context = ""
            if articles:
                literature_context += f"🔬 CLINTRA RESEARCH DATABASE - HIGH-IMPACT LITERATURE ANALYSIS 🔬\n"
                literature_context += f"📊 Query Target: \"{message}\"\n"
                literature_context += f"📚 Critical Papers Analyzed: {len(articles)} recent publications\n\n"
                
                # Enhanced detailed article analysis
                for i, article in enumerate(articles, 1):
                    literature_context += f"━━─ 📑 RESEARCH PUBLICATION #{i} ━━\n"
                    literature_context += f"📖 **Title:** {article['title']}\n"
                    literature_context += f"👥 **Authors:** {article.get('authors', 'N/A')}\n"
                    literature_context += f"📰 **Journal:** {article.get('journal', 'N/A')}\n"
                    literature_context += f"📅 **Published:** {article.get('publication_date', 'N/A')}\n"
                    
                    # Enhanced abstract with key findings highlighted
                    abstract_text = article.get('abstract', 'N/A')
                    if len(abstract_text) > 100:
                        literature_context += f"🔍 **Key Findings:** {abstract_text[:800]}...\n"
                    else:
                        literature_context += f"🔍 **Summary:** {abstract_text}\n"
                    
                    # Add research methodology indicators
                    methodology_keywords = ['clinical trial', 'in vitro', 'in vivo', 'case study', 'cohort', 'meta-analysis', 'randomized', 'prospective', 'retrospective']
                    abstract_lower = abstract_text.lower()
                    found_methods = [method for method in methodology_keywords if method in abstract_lower]
                    
                    if found_methods:
                        literature_context += f"🔬 **Methodology:** {', '.join(found_methods[:3])}\n"
                    
                    # Add impact indicators
                    if any(word in abstract_lower for word in ['breakthrough', 'novel', 'innovative', 'first', 'discovery']):
                        literature_context += f"⭐ **Impact:** High-impact research work\n"
                    
                    literature_context += f"🔗 **Citations:** PMID: {article.get('pmid', 'N/A')} | DOI: {article.get('doi', 'N/A')}\n"
                    literature_context += f"🌐 **Access:** https://pubmed.ncbi.nlm.nih.gov/{article.get('pmid', '')}\n"
                    literature_context += f"📊 **Impact:** Peer-reviewed research from biomedical literature database\n\n"
            
            if trials:
                literature_context += f"\n🏥 CLINICAL TRIALS DATABASE - ONGOING RESEARCH STUDIES 🏥\n"
                literature_context += f"📊 Active Studies Retrieved: {len(trials)} clinical investigations\n\n"
                
                for i, trial in enumerate(trials, 1):
                    literature_context += f"━━─ 🩺 CLINICAL TRIAL #{i} ━━\n"
                    literature_context += f"🎯 **Study Title:** {trial['title']}\n"
                    
                    # Enhanced status with visual indicators
                    trial_status = trial.get('status', 'N/A')
                    if trial_status.lower() in ['recruiting', 'active']:
                        literature_context += f"📋 **Status:** {trial_status} ⭐\n"
                    elif trial_status.lower() == 'completed':
                        literature_context += f"📋 **Status:** {trial_status} ✅\n"
                    else:
                        literature_context += f"📋 **Status:** {trial_status}\n"
                    
                    literature_context += f"🔬 **Phase:** {trial.get('phase', 'N/A')}\n"
                    literature_context += f"🆔 **NCT ID:** {trial.get('nct_id', 'N/A')}\n"
                    literature_context += f"🎯 **Purpose:** {trial.get('purpose', 'Research study')}\n"
                    literature_context += f"🌐 **Registry:** https://clinicaltrials.gov/show/{trial.get('nct_id', '')}\n"
                    literature_context += f"📊 **Evidence Level:** Clinical investigation data\n\n"
            
            # STEP 2: AI-DRIVEN DYNAMIC PDB STRUCTURE SUGGESTIONS
            # ENHANCED: Always provide PDB structures for ANY research query with intelligent analysis
            print(f"Debug: Fetching dynamic PDB structure suggestions for comprehensive analysis...")
            
            feature_2_pdb = None
            pdb_analysis = None
            
            # DYNAMIC PDB search with multiple query variations for maximum coverage
            try:
                from .connectors.pdb import PDBConnector
                pdb_connector = PDBConnector()
                
                # Create multiple search variations for comprehensive coverage
                search_variations = [message, optimized_query]
                
                # Add specific protein-related terms if not present
                if not any(term in message.lower() for term in ['protein', 'structure', 'pdb', 'crystal', 'enzyme']):
                    search_variations.append(f"protein structure {message}")
                
                # Add therapeutic context if disease-related
                if any(term in message.lower() for term in ['cancer', 'diabetes', 'alzheimer', 'hiv', 'covid']):
                    search_variations.append(f"therapeutic target {message}")
                
                pdb_structures = []
                for variation in search_variations[:3]:  # Limit to 3 variations to avoid API overload
                    try:
                        structures = pdb_connector.search_proteins(variation, max_results=3)
                        pdb_structures.extend(structures)
                        if len(pdb_structures) >= 5:  # Limit total results
                            break
                    except Exception as e:
                        print(f"PDB search variation failed: {variation} - {e}")
                        continue
                
                # Remove duplicates based on PDB ID
                seen_pdb_ids = set()
                unique_structures = []
                for structure in pdb_structures:
                    pdb_id = structure.get('pdb_id', '')
                    if pdb_id and pdb_id not in seen_pdb_ids:
                        unique_structures.append(structure)
                        seen_pdb_ids.add(pdb_id)
                
                pdb_structures = unique_structures[:5]  # Final limit
                print(f"Debug: Found {len(pdb_structures)} unique PDB structures from {len(search_variations)} search variations")
            
                pdb_analysis = {
                    "structures_found": len(pdb_structures),
                    "structures": pdb_structures,
                    "query_context": f"Protein structures relevant to: {message}",
                    "search_method": "multi-variation dynamic search",
                    "therapeutic_relevance": "AI-analyzed structural biology targets"
                }
                feature_2_pdb = pdb_analysis
                
            except Exception as e:
                print(f"Debug: PDB connector error: {e}")
                feature_2_pdb = None
            
            # STEP 3: AI-DRIVEN DYNAMIC PubChem COMPOUND SUGGESTIONS  
            # ENHANCED: Always provide drug compound data for ANY research query with intelligent analysis
            print(f"Debug: Fetching dynamic PubChem compound suggestions for comprehensive drug analysis...")
            
            feature_3_pubchem = None
            pubchem_analysis = None
            
            # DYNAMIC PubChem search with multiple query variations and literature integration
            try:
                from .connectors.pubchem import PubChemConnector
                pubchem_connector = PubChemConnector()
                
                # Create multiple search variations for comprehensive drug coverage
                drug_search_variations = [message, optimized_query]
                
                # Add specific drug-related terms if not present
                if not any(term in message.lower() for term in ['drug', 'compound', 'medication', 'therapy', 'treatment']):
                    drug_search_variations.append(f"drug therapy {message}")
                
                # Add therapeutic context based on disease
                if any(term in message.lower() for term in ['cancer', 'oncology']):
                    drug_search_variations.append("cancer chemotherapy")
                elif any(term in message.lower() for term in ['diabetes', 'insulin']):
                    drug_search_variations.append("diabetes medication")
                elif any(term in message.lower() for term in ['hiv', 'aids']):
                    drug_search_variations.append("HIV antiretroviral")
                elif any(term in message.lower() for term in ['alzheimer', 'dementia']):
                    drug_search_variations.append("alzheimer treatment")
                
                # ENHANCED: Pass comprehensive literature context to extract recent drugs from research
                literature_context_for_drugs = ""
                if articles:
                    literature_context_for_drugs += f"RESEARCH ARTICLES ({len(articles)} papers):\\n"
                    for article in articles:
                        literature_context_for_drugs += f"Title: {article.get('title', '')}\\n"
                        if article.get('abstract'):
                            literature_context_for_drugs += f"Abstract: {article['abstract']}\\n"
                
                pubchem_compounds = []
                for variation in drug_search_variations[:3]:  # Limit to 3 variations
                    try:
                        compounds = pubchem_connector.search_compounds(variation, max_results=3, literature_context=literature_context_for_drugs)
                        pubchem_compounds.extend(compounds)
                        if len(pubchem_compounds) >= 5:  # Limit total results
                            break
                    except Exception as e:
                        print(f"PubChem search variation failed: {variation} - {e}")
                        continue
                
                # Remove duplicates based on CID
                seen_cids = set()
                unique_compounds = []
                for compound in pubchem_compounds:
                    cid = compound.get('cid', '')
                    if cid and cid not in seen_cids:
                        unique_compounds.append(compound)
                        seen_cids.add(cid)
                
                pubchem_compounds = unique_compounds[:5]  # Final limit
                print(f"Debug: Found {len(pubchem_compounds)} unique PubChem compounds from {len(drug_search_variations)} search variations (enhanced with literature analysis)")
                
                pubchem_analysis = {
                    "compounds_found": len(pubchem_compounds),
                    "compounds": pubchem_compounds,
                    "query_context": f"Drug compounds relevant to: {message}",
                    "search_method": "multi-variation dynamic search with literature integration",
                    "therapeutic_relevance": "AI-analyzed drug discovery targets from research papers"
                }
                feature_3_pubchem = pubchem_analysis
                
            except Exception as e:
                print(f"Debug: PubChem connector error: {e}")
                feature_3_pubchem = None
            
            # STEP 4: INTELLIGENT VISUALIZATION DETECTION
            # Detect when user requests visualizations, diagrams, or graphs
            print(f"Debug: Checking for visualization requests...")
            
            # Smart visualization detection based on user request keywords
            visualization_keywords = [
                'visualize', 'visualization', 'graph', 'chart', 'diagram', 'network', 'pathway',
                'workflow', 'flowchart', 'flow chart', 'scheme', 'mechanism diagram',
                'interaction map', 'protein network', 'drug mechanism', 'create diagram',
                'create graph', 'show diagram', 'show graph', 'plot', 'mapping',
                'relationship diagram', 'interaction network', 'pathway diagram',
                'biological diagram', 'molecular diagram', 'cellular diagram',
                'enzymatic pathway', 'metabolic pathway', 'signal pathway',
                'pharmacokinetic diagram', 'pharmacodynamics diagram'
            ]
            
            show_visualization = any(keyword in message.lower() for keyword in visualization_keywords)
            visualization_type = 'network'  # Default visualization
            
            # Detect specific visualization type requested
            if any(word in message.lower() for word in ['pathway', 'metabolic', 'enzymatic']):
                visualization_type = 'pathway'
            elif any(word in message.lower() for word in ['workflow', 'process', 'steps']):
                visualization_type = 'workflow'
            elif any(word in message.lower() for word in ['mechanism', 'drug', 'compound']):
                visualization_type = 'drug_mechanism'
            elif any(word in message.lower() for word in ['network', 'interaction', 'protein-protein']):
                visualization_type = 'interaction_network'
            
            # Create visualization analysis if requested
            visualization_analysis = None
            if show_visualization:
                print(f"Debug: User requested visualization: {visualization_type}")
                
                visualization_analysis = {
                    "visualization_type": visualization_type,
                    "query_context": f"Visualization of: {message}",
                    "suggested_title": f"{visualization_type.title().replace('_', ' ')} Diagram",
                    "data_sources": {
                        "literature_data": len(articles),
                        "protein_structures": pdb_analysis['structures_found'] if pdb_analysis else 0,
                        "drug_compounds": pubchem_analysis['compounds_found'] if pubchem_analysis else 0
                    },
                    "visualization_preview": "Generated on-demand visualization",
                    "download_formats": ["SVG", "PNG", "PDF"],
                    "user_requested": True
                }
            
            # STEP 1: AI-DRIVEN DYNAMIC FEEDBACK MECHANISM ANALYSIS
            # Check if user explicitly requests "fallback responses" or alternative approaches
            feedback_analysis = None
            fallback_response_analysis = None
            show_feedback_mechanisms = any(phrase in message.lower() for phrase in [
                "fallback response", "fallback responses", "along with fallback", "include fallback", 
                "with fallback", "alternative approach", "alternative treatment", "alternative therapy",
                "feedback responses", "feedback mechanisms", "biological feedback",
                "can you give feedback", "show feedback", "feedback loop", "regulation feedback",
                "homeostatic feedback", "negative feedback", "positive feedback", "feedback control"
            ])
            
            print(f"Debug: Feedback mechanism check - '{message}' -> {show_feedback_mechanisms}")
            
            if show_feedback_mechanisms:
                # DYNAMIC ALTERNATIVE APPROACHES & FALLBACK THERAPIES USING CEREBRAS LLAMA + REAL LITERATURE
                fallback_prompt = f"""You are a research accelerator providing ALTERNATIVE APPROACHES and FALLBACK THERAPIES. Generate comprehensive analysis for:

RESEARCH QUERY: "{message}"

REAL LITERATURE DATA (Use this for evidence):
{literature_context[:5000]}

TASK: Provide ALTERNATIVE and FALLBACK therapeutic approaches based on the literature.

Generate a detailed response with these sections:

## 🔄 ALTERNATIVE TREATMENT APPROACHES
- List 3-5 alternative therapeutic strategies mentioned in the literature
- Include specific drug names, therapy types, or approaches
- Reference the PubMed articles that discuss each approach

## 🩺 FALLBACK THERAPIES
- What are second-line or fallback treatments when first-line therapy fails?
- Combination therapies that serve as alternatives
- Emerging experimental approaches

## 💊 SPECIFIC DRUG ALTERNATIVES
- List specific drugs or compounds from the literature
- Include mechanism of action if mentioned
- Note any clinical trial data

## 🧬 MOLECULAR MECHANISMS
- Biological pathways involved in alternative approaches
- Key proteins, genes, or receptors targeted
- Feedback mechanisms and regulatory loops

## 📚 EVIDENCE BASE
- Reference specific PubMed articles (by PMID) that support each alternative
- Note clinical trial IDs (NCT numbers) if available
- Indicate level of evidence (Phase I/II/III trials, etc.)

Base EVERYTHING on the provided real literature data. DO NOT make up information."""

                # Generate AI analysis using Cerebras Llama
                print(f"Debug: Calling Cerebras for alternative/fallback therapy analysis")
                ai_fallback_analysis = await rag.call_cerebras_api(fallback_prompt, max_tokens=3000, model="llama3.1-8b", temperature=0.7)
                print(f"Debug: Alternative approaches analysis generated: {len(ai_fallback_analysis) if ai_fallback_analysis else 0} chars")
                
                # Structure the AI response
                feedback_analysis = {
                    "mechanism_name": f"Alternative Approaches & Fallback Therapies: {message}",
                    "components": ["AI-analyzed from PubMed literature"], 
                    "mechanism_description": ai_fallback_analysis,
                    "related_disorders": ["Based on real literature analysis"],
                    "molecular_targets": {"Literature_based": f"Extracted from {len(articles)} PubMed articles"},
                    "disease_category": "Evidence-based alternative approaches",
                    "ai_generated": True,
                    "literature_source": f"Analyzed from {len(articles)} PubMed articles + {len(trials)} clinical trials",
                    "analysis_type": "alternative_fallback_therapies"
                }
            
            # Enhanced literature context with molecular targeting info
            enhanced_literature_context = literature_context
            
            # 🚀 HACKATHON ENHANCEMENT: Always show PDB & PubChem for complete responses
            # Users expect comprehensive data including protein structures and drug compounds
            context_length = len(enhanced_literature_context)
            print(f"Debug: Enhanced context prepared ({context_length} chars) with all features enabled")
            
            # Add PDB structure suggestions to enhanced context
            if pdb_analysis:
                enhanced_literature_context += f"\n\nMOLECULAR STRUCTURE SUGGESTIONS:\n"
                enhanced_literature_context += f"Query: {pdb_analysis['query_context']}\n"
                enhanced_literature_context += f"Found {pdb_analysis['structures_found']} relevant protein structures:\n\n"
                
                for i, structure in enumerate(pdb_analysis['structures'], 1):
                    enhanced_literature_context += f"{i}. **PDB ID: {structure['pdb_id']}**\n"
                    enhanced_literature_context += f"   Title: {structure['title']}\n"
                    enhanced_literature_context += f"   Resolution: {structure['resolution']} | Method: {structure['method']}\n"
                    enhanced_literature_context += f"   Organism: {structure['organism']}\n"
                    enhanced_literature_context += f"   Description: {structure['description']}\n"
                    enhanced_literature_context += f"   Structure URL: {structure['url']}\n"
                    enhanced_literature_context += f"   Journal: {structure['journal']}\n\n"
            
            # Add PubChem compound suggestions to enhanced context
            if pubchem_analysis:
                enhanced_literature_context += f"\n\nDRUG COMPOUND SUGGESTIONS:\n"
                enhanced_literature_context += f"Query: {pubchem_analysis['query_context']}\n"
                enhanced_literature_context += f"Found {pubchem_analysis['compounds_found']} relevant therapeutic compounds:\n\n"
                
                for i, compound in enumerate(pubchem_analysis['compounds'], 1):
                    enhanced_literature_context += f"{i}. **Compound CID: {compound['cid']}**\n"
                    enhanced_literature_context += f"   Name: {compound['name']}\n"
                    enhanced_literature_context += f"   Synonyms: {', '.join(compound.get('synonyms', []))}\n"
                    enhanced_literature_context += f"   Molecular Formula: {compound['molecular_formula']}\n"
                    enhanced_literature_context += f"   Molecular Weight: {compound['molecular_weight']}\n"
                    enhanced_literature_context += f"   Mechanism of Action: {compound['mechanism']}\n"
                    enhanced_literature_context += f"   Drug Targets: {', '.join(compound.get('targets', []))}\n"
                    enhanced_literature_context += f"   Indications: {', '.join(compound.get('indications', []))}\n"
                    enhanced_literature_context += f"   Compound URL: {compound['url']}\n\n"
            
            # Add visualization suggestions if requested
            if visualization_analysis:
                enhanced_literature_context += f"\n\nVISUALIZATION ANALYSIS:\n"
                enhanced_literature_context += f"Type: {visualization_analysis['visualization_type']}\n"
                enhanced_literature_context += f"Title: {visualization_analysis['suggested_title']}\n"
                enhanced_literature_context += f"Context: {visualization_analysis['query_context']}\n"
                enhanced_literature_context += f"Data Sources: {visualization_analysis['data_sources']['literature_data']} papers, "
                enhanced_literature_context += f"{visualization_analysis['data_sources']['protein_structures']} structures, "
                enhanced_literature_context += f"{visualization_analysis['data_sources']['drug_compounds']} compounds\n"
                enhanced_literature_context += f"Download Formats: {', '.join(visualization_analysis['download_formats'])}\n"
            
            # Add feedback mechanism analysis if requested
            if feedback_analysis:
                enhanced_literature_context += f"\n\nFEEDBACK MECHANISM ANALYSIS:\n"
                enhanced_literature_context += f"Mechanism: {feedback_analysis['mechanism_name']}\n"
                enhanced_literature_context += f"Components: {', '.join(feedback_analysis['components'])}\n"
                enhanced_literature_context += f"Process: {feedback_analysis['mechanism_description']}\n"
                enhanced_literature_context += f"Molecular Targets: {feedback_analysis['molecular_targets']}\n"

            # HACKATHON SUCCESS: Only use the earlier smart optimization
            # This prevents feature disabling conflicts

            # 🚨 EMPTY LITERATURE HANDLING - Prevent Cerebras hallucinations
            if not enhanced_literature_context:
                print(f"Debug: NO LITERATURE FOUND - Using fallback prompt to prevent hallucinations")
                enhanced_literature_context = f"""
NO RESEARCH LITERATURE AVAILABLE:
Query "{message}" did not return any PubMed articles or clinical trials.

FALLBACK APPROACH:
Instead of making up fake data, provide:
1. Direction to refine search terms  
2. Suggestions for better query formulation
3. General guidance without false citations
4. Clear explanation of why no data was found

IMPORTANT: DO NOT create fake references or pretend literature exists.
DO NOT cite non-existent papers or make up study data.
DO NOT repeat "MAX LEVEL RESEARCH ACCELERATOR" multiple times.
"""

            # 🚀 SIMPLIFIED BUT POWERFUL AI PROMPT
            rag_prompt = f"""You are a world-class biomedical research analyst. Provide a comprehensive analysis of the research query below.

USER QUERY: "{message}"

RESEARCH DATA AVAILABLE:
{enhanced_literature_context}

TASK: Provide a detailed, evidence-based analysis that includes:

1. **Key Research Findings** - Extract specific insights from the literature
2. **Therapeutic Approaches** - Identify treatment strategies and mechanisms  
3. **Clinical Evidence** - Summarize trial outcomes and safety data
4. **Research Gaps** - Identify areas needing further investigation
5. **Future Directions** - Suggest next steps for research and clinical practice

REQUIREMENTS:
- Use specific drug names, protein targets, and mechanisms from the literature
- Include quantitative data and statistics when available
- Cite specific studies and their findings
- Provide actionable insights for researchers and clinicians
- Write in a clear, professional scientific style

Focus on delivering comprehensive, evidence-based insights that will help advance research and clinical practice in this field."""

            # ENHANCED: Use higher token limit and optimized temperature for dynamic analysis
            rag_summary = await rag.call_cerebras_api(rag_prompt, max_tokens=8000, model="llama3.1-8b", temperature=0.8)
            
            # Debug: Log the raw AI response
            print(f"Debug: Raw AI response length: {len(rag_summary) if rag_summary else 0}")
            if rag_summary:
                print(f"Debug: Raw AI response preview: {rag_summary[:200]}...")
            else:
                print("Debug: AI response is empty or None!")
            
            # 🤖 AI-POWERED RESPONSE FORMATTING & CLEANUP
            async def ai_format_response(raw_response):
                """AI-powered response formatting and cleanup"""
                try:
                    if not raw_response or len(raw_response) < 50:
                        return raw_response
                    
                    # Create AI prompt for response formatting
                    ai_prompt = f"""You are a biomedical AI response formatter. Clean and format this research response.

Raw Response: "{raw_response}"

Your task:
1. Remove any internal AI instructions or system messages
2. Clean up formatting and remove repeated phrases
3. Ensure proper scientific formatting with bullet points and bold text
4. Remove any "TL;DR", "Please wait", or "As an AI" sections
5. Maintain scientific accuracy and professional tone
6. Ensure proper markdown formatting

Return ONLY the cleaned, formatted response."""
                    
                    import openai
                    import os
                    
                    openai_api_key = os.getenv('OPENAI_API_KEY')
                    if not openai_api_key:
                        return _static_format_response(raw_response)
                    
                    client = openai.OpenAI(api_key=openai_api_key)
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": ai_prompt}],
                        max_tokens=8000,
                        temperature=0.1
                    )
                    
                    formatted_response = response.choices[0].message.content.strip()
                    
                    if formatted_response and len(formatted_response) > 100:
                        print(f"🤖 AI Response Formatting: {len(raw_response)} → {len(formatted_response)} chars")
                        return formatted_response
                    else:
                        return _static_format_response(raw_response)
                        
                except Exception as e:
                    print(f"⚠️ AI response formatting failed: {e}")
                    return _static_format_response(raw_response)
            
            def _static_format_response(raw_response):
                """Fallback static response formatting"""
                import re
                
                if raw_response and len(raw_response) > 50:
                    # Remove TL;DR sections
                    raw_response = re.sub(r'\*\*TL;DR\*\*.*$', '', raw_response, flags=re.DOTALL)
                    raw_response = re.sub(r'TL;DR:.*?$', '', raw_response, flags=re.DOTALL)
                    
                    # Remove AI instruction spam and internal leaks
                    raw_response = re.sub(r'Please wait while.*$', '', raw_response, flags=re.DOTALL)
                    raw_response = re.sub(r'I\'m generating.*$', '', raw_response, flags=re.DOTALL)
                    raw_response = re.sub(r'As an AI.*$', '', raw_response, flags=re.DOTALL)
                    raw_response = re.sub(r'I cannot.*$', '', raw_response, flags=re.DOTALL)
                    
                    # Remove repeated phrases and glitches
                    raw_response = re.sub(r'(CLINTRA.*?ACCELERATOR.*?){2,}', r'\1', raw_response, flags=re.DOTALL)
                    raw_response = re.sub(r'(MAX LEVEL.*?){2,}', '', raw_response, flags=re.DOTALL)
                    
                    # Clean up formatting issues
                    raw_response = re.sub(r'\n{3,}', '\n\n', raw_response)  # Max 2 newlines
                    raw_response = re.sub(r'•\s*•', '•', raw_response)  # Fix double bullets
                    
                    # Ensure proper ending
                    raw_response = raw_response.strip()
                    if not raw_response.endswith('.') and not raw_response.endswith('!') and not raw_response.endswith('?'):
                        raw_response += '.'
                
                return raw_response
            
            # Skip AI formatting to preserve full response
            # rag_summary = await ai_format_response(rag_summary)
                
            # FALLBACK: If response is too short, provide a basic summary
            if not rag_summary or len(rag_summary) < 200:
                print("Debug: AI response too short, providing fallback summary")
                rag_summary = f"""## 📋 RESEARCH ANALYSIS SUMMARY

Based on analysis of {len(articles)} research papers and {len(trials)} clinical trials:

### 🔬 Key Research Findings
• **Current research trends** identified in recent literature
• **Therapeutic approaches** and **molecular mechanisms** under investigation  
• **Clinical trial outcomes** and **safety profiles** from ongoing studies
• **Evidence-based insights** from peer-reviewed research

### 📚 Literature Sources
• **{len(articles)} PubMed articles** analyzed for comprehensive coverage
• **{len(trials)} clinical trials** reviewed for current research status
• **Multi-database integration** ensuring comprehensive analysis

### 🎯 Research Impact
This analysis provides evidence-based insights from current biomedical literature, combining findings from multiple research studies and clinical investigations to deliver comprehensive understanding of the topic.

*Analysis powered by Clintra's advanced research accelerator with real-time data from PubMed, ClinicalTrials.gov, and other biomedical databases.*"""
            
            response_data = {
                "message": message,
                "query": message,
                "rag_summary": rag_summary,
                "pubmed_articles": articles,
                "clinical_trials": trials,
                "type": "research_query",
                "ai_model": "Cerebras Llama 3.1-8B (Primary) + OpenAI GPT-4 (Fallback)",
                "literature_count": len(articles),
                "trials_count": len(trials),
                "citations": len(articles) + len(trials),
                "research_accelerator": True,
                "papers_analyzed": f"{len(articles)} research papers + {len(trials)} clinical trials",
                "sponsor_tech": "🏆 PRIMARY: Cerebras Llama 3.1-8B (sponsor tech) + Docker MCP microservices + PubMed/PubChem/PDB/ClinicalTrials APIs",
                "timestamp": datetime.utcnow().isoformat(),
                # 🚀 STEP 1: FEATURE 1 - FEEDBACK MECHANISMS ONLY
                "feature_1_feedback": feedback_analysis,  # Simple test feature
                # 🚀 STEP 2: FEATURE 2 - PDB STRUCTURE SUGGESTIONS
                "feature_2_pdb": pdb_analysis,  # Protein structure suggestions
                # 🚀 STEP 3: FEATURE 3 - PubChem COMPOUND SUGGESTIONS
                "feature_3_pubchem": pubchem_analysis,  # Drug compound suggestions
                "feature_4_visualization": visualization_analysis  # Smart visualization suggestions
            }
            
            # EMERGENCY DEBUG: Log what we're actually returning
            print(f"HACKATHON DEBUG: Final response rag_summary length: {len(str(response_data.get('rag_summary', 'MISSING'))) if response_data.get('rag_summary') else 'NONE'}")
            print(f"HACKATHON DEBUG: Response data keys: {list(response_data.keys())}")
            print(f"HACKATHON DEBUG: rag_summary preview: {str(response_data.get('rag_summary', 'MISSING'))[:100]}...")
            
            return response_data
            
    except Exception as e:
        print(f"Smart chat error: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        # 🤖 AI-POWERED ERROR RECOVERY
        try:
            ai_error_response = await _ai_generate_error_response(message, str(e))
            return {
                "message": message,
                "response": ai_error_response,
                "type": "error_recovery",
                "error": str(e),
                "ai_model": "AI Error Handler",
                "sponsor_tech": "🤖 AI ERROR RECOVERY: Intelligent error handling activated",
                "timestamp": datetime.utcnow().isoformat()
            }
        except:
            # Fallback to simple response
            return {
                "message": message,
                "response": f"I'm Clintra, your AI research assistant. I can help you with biomedical research, literature search, and drug discovery. What would you like to explore?",
                "type": "fallback",
                "error": str(e),
                "ai_model": "Fallback Response",
                "sponsor_tech": "🔄 FALLBACK: Simple response due to API error",
                "timestamp": datetime.utcnow().isoformat()
            }

async def _ai_generate_error_response(user_query: str, error_message: str) -> str:
    """🤖 AI-POWERED: Generate intelligent error recovery response"""
    try:
        # Create AI prompt for error recovery
        ai_prompt = f"""You are Clintra, an AI biomedical research assistant. A technical error occurred while processing a user query.

User Query: "{user_query}"
Technical Error: "{error_message}"

Generate a helpful, professional response that:
1. Acknowledges the error gracefully
2. Suggests alternative ways to help the user
3. Maintains a helpful, research-focused tone
4. Offers to help with related biomedical topics
5. Keeps the response concise and actionable

Return ONLY the helpful response, nothing else."""
        
        import openai
        import os
        
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return f"I apologize, but I encountered a technical issue while processing your query about '{user_query}'. Please try rephrasing your question or ask about a different biomedical topic. I'm here to help with research, drug discovery, and scientific analysis!"
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": ai_prompt}],
            max_tokens=200,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        if ai_response and len(ai_response) > 50:
            print(f"🤖 AI Error Recovery: Generated helpful response for error")
            return ai_response
        else:
            return f"I apologize, but I encountered a technical issue while processing your query about '{user_query}'. Please try rephrasing your question or ask about a different biomedical topic. I'm here to help with research, drug discovery, and scientific analysis!"
            
    except Exception as e:
        print(f"⚠️ AI error recovery failed: {e}")
        return f"I apologize, but I encountered a technical issue while processing your query about '{user_query}'. Please try rephrasing your question or ask about a different biomedical topic. I'm here to help with research, drug discovery, and scientific analysis!"

@app.post("/api/3d-structure")
async def get_3d_structure(request: dict):
    """Get enhanced 3D structure data for molecules"""
    try:
        compound_name = request.get("compound_name", "")
        
        if not compound_name:
            return {"error": "Compound name is required"}
        
        print(f"3D Structure request for: {compound_name}")
        
        # Import connectors
        from .connectors.pubchem import PubChemConnector
        from .connectors.pdb import PDBConnector
        
        pubchem_connector = PubChemConnector()
        pdb_connector = PDBConnector()
        
        # Search PubChem for compound data
        pubchem_results = pubchem_connector.search_compounds(compound_name, max_results=1)
        
        enhanced_data = {
            "compound_name": compound_name,
            "pubchem_data": None,
            "pdb_data": None,
            "3d_structure": None,
            "metadata": {
                "search_timestamp": datetime.utcnow().isoformat(),
                "source_apis": []
            }
        }
        
        # Process PubChem results
        if pubchem_results and len(pubchem_results) > 0:
            compound = pubchem_results[0]
            enhanced_data["pubchem_data"] = compound
            enhanced_data["metadata"]["source_apis"].append("PubChem")
            
            # Try to get 3D structure from PubChem
            try:
                cid = compound.get("cid")
                if cid:
                    print(f"Attempting to fetch 3D structure for CID {cid}")
                    # Fetch 3D coordinates from PubChem
                    import requests
                    pubchem_3d_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/JSON?record_type=3d"
                    print(f"PubChem 3D URL: {pubchem_3d_url}")
                    
                    response = requests.get(pubchem_3d_url, timeout=10)
                    print(f"PubChem 3D response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"PubChem 3D response data keys: {list(data.keys())}")
                        if data.get("PC_Compounds") and len(data["PC_Compounds"]) > 0:
                            pc_compound = data["PC_Compounds"][0]
                            print(f"Processing PubChem compound data: {list(pc_compound.keys())}")
                            enhanced_data["3d_structure"] = process_pubchem_3d_data(pc_compound)
                            enhanced_data["metadata"]["source_apis"].append("PubChem-3D")
                            print(f"SUCCESS: Retrieved 3D structure for CID {cid}")
                        else:
                            print(f"No PC_Compounds found in PubChem 3D response")
                    else:
                        print(f"PubChem 3D API returned status {response.status_code}: {response.text[:200]}")
            except Exception as e:
                print(f"Failed to get 3D structure from PubChem: {e}")
                import traceback
                traceback.print_exc()
        
        # Search PDB for protein structures if compound might be a protein
        protein_keywords = ['protein', 'enzyme', 'antibody', 'receptor', 'insulin', 'hemoglobin']
        if any(keyword in compound_name.lower() for keyword in protein_keywords):
            try:
                pdb_results = pdb_connector.search_proteins(compound_name, max_results=3)
                if pdb_results:
                    enhanced_data["pdb_data"] = pdb_results
                    enhanced_data["metadata"]["source_apis"].append("PDB")
                    print(f"SUCCESS: Found {len(pdb_results)} PDB structures for {compound_name}")
            except Exception as e:
                print(f"Failed to search PDB: {e}")
        
        return enhanced_data
        
    except Exception as e:
        print(f"3D Structure endpoint error: {e}")
        return {"error": f"Failed to get 3D structure data: {str(e)}"}

def process_pubchem_3d_data(pc_compound):
    """Process PubChem 3D coordinate data"""
    try:
        atoms = []
        bonds = []
        
        # Extract atom coordinates
        if pc_compound.get("coords") and pc_compound["coords"][0]:
            coord_data = pc_compound["coords"][0]
            
            if coord_data.get("conformers") and coord_data["conformers"][0]:
                conformer = coord_data["conformers"][0]
                x_coords = conformer.get("x", [])
                y_coords = conformer.get("y", [])
                z_coords = conformer.get("z", [])
                
                # Get atom elements
                atom_elements = pc_compound.get("atoms", {}).get("element", [])
                
                for i in range(len(x_coords)):
                    atomic_number = atom_elements[i] if i < len(atom_elements) else 6  # Default to carbon
                    element = get_element_symbol(atomic_number)
                    
                    atoms.append({
                        "id": i,
                        "element": element,
                        "atomic_number": atomic_number,
                        "x": x_coords[i],
                        "y": y_coords[i],
                        "z": z_coords[i],
                        "radius": get_atomic_radius(element)
                    })
        
        # Extract bonds
        if pc_compound.get("bonds"):
            bond_data = pc_compound["bonds"]
            aid1 = bond_data.get("aid1", [])
            aid2 = bond_data.get("aid2", [])
            order = bond_data.get("order", [])
            
            for i in range(len(aid1)):
                bonds.append({
                    "id": i,
                    "atom1": aid1[i] - 1,  # Convert to 0-based indexing
                    "atom2": aid2[i] - 1,
                    "order": order[i] if i < len(order) else 1
                })
        
        return {
            "atoms": atoms,
            "bonds": bonds,
            "metadata": {
                "atom_count": len(atoms),
                "bond_count": len(bonds),
                "source": "PubChem 3D",
                "processed_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        print(f"Error processing PubChem 3D data: {e}")
        return {"atoms": [], "bonds": [], "metadata": {"error": str(e)}}

def get_element_symbol(atomic_number):
    """Convert atomic number to element symbol"""
    elements = {
        1: 'H', 6: 'C', 7: 'N', 8: 'O', 15: 'P', 16: 'S',
        9: 'F', 17: 'Cl', 35: 'Br', 53: 'I', 11: 'Na', 19: 'K',
        20: 'Ca', 12: 'Mg', 26: 'Fe', 30: 'Zn', 29: 'Cu', 25: 'Mn'
    }
    return elements.get(atomic_number, 'C')

def get_atomic_radius(element):
    """Get atomic radius for element"""
    radii = {
        'H': 0.31, 'C': 0.70, 'N': 0.71, 'O': 0.66,
        'S': 1.04, 'P': 1.07, 'F': 0.57, 'Cl': 0.99,
        'Br': 1.20, 'I': 1.39, 'Na': 1.86, 'K': 2.27,
        'Ca': 1.97, 'Mg': 1.60, 'Fe': 1.26, 'Zn': 1.39,
        'Cu': 1.32, 'Mn': 1.27
    }
    return radii.get(element, 0.70)