import os
import numpy as np
from typing import List, Dict, Any, Optional
try:
    import pinecone
    # For pinecone-client 2.2.4, use the init function instead of Pinecone class
    Pinecone = pinecone.init
    ServerlessSpec = None  # Not available in this version
except ImportError:
    pinecone = None
    Pinecone = None
    ServerlessSpec = None
try:
    import openai
    from langchain.embeddings import OpenAIEmbeddings
except ImportError:
    openai = None
    OpenAIEmbeddings = None
from langchain.vectorstores import Pinecone as LangchainPinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import asyncio
import logging

logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self):
        self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
        self.pinecone_environment = os.getenv('PINECONE_ENVIRONMENT', 'gcp-starter')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.index_name = "clintra-biomedical"
        self.dimension = 1536  # OpenAI embedding dimension
        self.pinecone_available = pinecone is not None
        self.metric = "cosine"
        
        # Initialize Pinecone
        if self.pinecone_api_key and self.pinecone_available:
            pinecone.init(api_key=self.pinecone_api_key, environment=self.pinecone_environment)
            self.pc = pinecone
            self._initialize_index()
        else:
            logger.warning("Pinecone API key not found. Vector search will be disabled.")
            self.pc = None
        
        # Initialize embeddings
        if self.openai_api_key and OpenAIEmbeddings is not None:
            self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        else:
            logger.warning("OpenAI API key not found or OpenAI not available. Using mock embeddings.")
            self.embeddings = None
    
    def _initialize_index(self):
        """Initialize or connect to Pinecone index."""
        if not self.pinecone_available:
            logger.warning("Pinecone not available. Skipping index initialization.")
            self.index = None
            return
            
        try:
            # For pinecone-client 2.2.4, use the index function
            self.index = pinecone.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone index: {e}")
            self.index = None
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Add documents to the vector database.
        
        Args:
            documents: List of documents with 'text', 'metadata' fields
            
        Returns:
            bool: Success status
        """
        if not self.index or not self.embeddings:
            logger.warning("Vector database not available. Skipping document addition.")
            return False
        
        try:
            # Prepare documents for embedding
            texts = []
            metadatas = []
            ids = []
            
            for i, doc in enumerate(documents):
                texts.append(doc['text'])
                metadatas.append(doc.get('metadata', {}))
                ids.append(f"doc_{i}_{hash(doc['text']) % 10000}")
            
            # Generate embeddings
            embeddings = self.embeddings.embed_documents(texts)
            
            # Prepare vectors for Pinecone
            vectors = []
            for i, (embedding, metadata, doc_id) in enumerate(zip(embeddings, metadatas, ids)):
                vectors.append({
                    'id': doc_id,
                    'values': embedding,
                    'metadata': {
                        **metadata,
                        'text': texts[i][:1000]  # Store first 1000 chars
                    }
                })
            
            # Upsert to Pinecone
            self.index.upsert(vectors=vectors)
            logger.info(f"Added {len(vectors)} documents to vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to vector database: {e}")
            return False
    
    def search_similar(self, query: str, top_k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of similar documents with scores
        """
        if not self.index or not self.embeddings:
            logger.warning("Vector database not available. Returning empty results.")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search Pinecone
            search_response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            results = []
            for match in search_response.matches:
                results.append({
                    'id': match.id,
                    'score': match.score,
                    'text': match.metadata.get('text', ''),
                    'metadata': {k: v for k, v in match.metadata.items() if k != 'text'}
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def add_literature_articles(self, articles: List[Dict[str, Any]]) -> bool:
        """
        Add PubMed articles to the vector database.
        
        Args:
            articles: List of PubMed articles
            
        Returns:
            bool: Success status
        """
        documents = []
        
        for article in articles:
            # Combine title and abstract for embedding
            text = f"{article.get('title', '')} {article.get('abstract', '')}"
            
            if text.strip():
                documents.append({
                    'text': text,
                    'metadata': {
                        'type': 'literature',
                        'pmid': article.get('pmid', ''),
                        'title': article.get('title', ''),
                        'authors': article.get('authors', ''),
                        'journal': article.get('journal', ''),
                        'publication_date': article.get('publication_date', ''),
                        'url': article.get('url', ''),
                        'mesh_terms': article.get('mesh_terms', [])
                    }
                })
        
        return self.add_documents(documents)
    
    def add_clinical_trials(self, trials: List[Dict[str, Any]]) -> bool:
        """
        Add clinical trials to the vector database.
        
        Args:
            trials: List of clinical trials
            
        Returns:
            bool: Success status
        """
        documents = []
        
        for trial in trials:
            # Combine title and conditions for embedding
            text = f"{trial.get('title', '')} {' '.join(trial.get('conditions', []))}"
            
            if text.strip():
                documents.append({
                    'text': text,
                    'metadata': {
                        'type': 'clinical_trial',
                        'nct_id': trial.get('nct_id', ''),
                        'title': trial.get('title', ''),
                        'status': trial.get('status', ''),
                        'phase': trial.get('phase', ''),
                        'conditions': trial.get('conditions', []),
                        'interventions': trial.get('interventions', []),
                        'sponsor': trial.get('sponsor', ''),
                        'url': trial.get('url', '')
                    }
                })
        
        return self.add_documents(documents)
    
    def semantic_search(self, query: str, data_types: List[str] = None, top_k: int = 10) -> Dict[str, List[Dict]]:
        """
        Perform semantic search across different data types.
        
        Args:
            query: Search query
            data_types: List of data types to search ('literature', 'clinical_trial')
            top_k: Number of results per type
            
        Returns:
            Dictionary with results by data type
        """
        if data_types is None:
            data_types = ['literature', 'clinical_trial']
        
        results = {}
        
        for data_type in data_types:
            filter_dict = {'type': data_type}
            type_results = self.search_similar(query, top_k=top_k, filter_dict=filter_dict)
            results[data_type] = type_results
        
        return results
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database index.
        
        Returns:
            Dictionary with index statistics
        """
        if not self.index:
            return {'error': 'Vector database not available'}
        
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vector_count': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness,
                'namespaces': stats.namespaces
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {'error': str(e)}

# Global instance
vector_db = VectorDatabase()
