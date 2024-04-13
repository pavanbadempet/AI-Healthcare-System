"""
RAG Module - Semantic Memory for Personalized Healthcare AI
============================================================
Uses FREE Gemini Embedding API (no local model needed = saves ~200MB)
"""
import os
import json
import pickle
import numpy as np
import logging
from typing import List, Dict, Optional, Any
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai

# --- Logging ---
logger = logging.getLogger(__name__)

# --- Constants ---
DB_FILE = os.path.join(os.path.dirname(__file__), "..", "models", "vector_store.pkl")
EMBEDDING_MODEL = "models/text-embedding-004"  # Free Gemini embedding model

# --- Gemini Embedding (FREE, no local model needed) ---
_configured = False

def get_embedding(text: str) -> List[float]:
    """
    Generate embedding using FREE Gemini API.
    No local model = saves ~200MB memory!
    """
    global _configured
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not found, using zero vector")
        return [0.0] * 768  # Return zero vector as fallback
    
    if not _configured:
        genai.configure(api_key=api_key)
        _configured = True
    
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return [0.0] * 768  # Fallback

def get_query_embedding(text: str) -> List[float]:
    """Generate embedding for search query."""
    global _configured
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return [0.0] * 768
    
    if not _configured:
        genai.configure(api_key=api_key)
        _configured = True
    
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Query embedding failed: {e}")
        return [0.0] * 768


class SimpleVectorStore:
    """
    Persistent vector store using Pickle + Scikit-Learn cosine similarity.
    Now powered by FREE Gemini embeddings!
    """
    
    def __init__(self):
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.vectors: List[List[float]] = []
        self.ids: List[str] = []
        self.load()

    def load(self) -> None:
        """Load from pickle file."""
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents', [])
                    self.metadatas = data.get('metadatas', [])
                    self.vectors = data.get('vectors', [])
                    self.ids = data.get('ids', [])
                logger.info(f"Loaded Vector Store: {len(self.ids)} records.")
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")

    def save(self) -> None:
        """Persist to pickle file."""
        try:
            os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
            with open(DB_FILE, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'metadatas': self.metadatas,
                    'vectors': self.vectors,
                    'ids': self.ids
                }, f)
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")

    def add(self, text: str, metadata: Dict[str, Any], record_id: str) -> None:
        """Add or update a document."""
        vector = get_embedding(text)
        
        if record_id in self.ids:
            idx = self.ids.index(record_id)
            self.documents[idx] = text
            self.metadatas[idx] = metadata
            self.vectors[idx] = vector
        else:
            self.documents.append(text)
            self.metadatas.append(metadata)
            self.vectors.append(vector)
            self.ids.append(record_id)
        
        self.save()

    def delete(self, record_id: str) -> bool:
        """Delete by ID."""
        if record_id in self.ids:
            idx = self.ids.index(record_id)
            self.documents.pop(idx)
            self.metadatas.pop(idx)
            self.vectors.pop(idx)
            self.ids.pop(idx)
            self.save()
            return True
        return False

    def search(self, query: str, filter_meta: Optional[Dict[str, Any]] = None, k: int = 3) -> List[str]:
        """Semantic search with user filtering."""
        if not self.vectors:
            return []
        
        query_vector = get_query_embedding(query)
        
        vec_matrix = np.array(self.vectors)
        q_vec = np.array([query_vector])
        
        # Cosine similarity
        sim_scores = cosine_similarity(q_vec, vec_matrix)[0]
        sorted_indices = sim_scores.argsort()[::-1]
        
        results = []
        count = 0
        
        for idx in sorted_indices:
            if sim_scores[idx] <= 0.0:
                break
            
            # Apply metadata filter
            match = True
            if filter_meta:
                for k_filter, v_filter in filter_meta.items():
                    if self.metadatas[idx].get(k_filter) != v_filter:
                        match = False
                        break
            
            if match:
                results.append(self.documents[idx])
                count += 1
                if count >= k:
                    break
        
        return results


# --- Singleton ---
_store = None

def get_vector_store() -> SimpleVectorStore:
    global _store
    if _store is None:
        _store = SimpleVectorStore()
    return _store


# --- Public API ---

def add_checkup_to_db(user_id: str, record_id: str, record_type: str, data: dict, prediction: str, timestamp: str) -> bool:
    """Index a health checkup record."""
    try:
        data_str = ", ".join([f"{k}: {v}" for k, v in data.items()])
        document_text = (
            f"User: {user_id}\n"
            f"Date: {timestamp}\n"
            f"Checkup Type: {record_type}\n"
            f"Result: {prediction}\n"
            f"Clinical Data: {data_str}"
        )
        
        get_vector_store().add(document_text, {
            "user_id": str(user_id),
            "record_id": str(record_id),
            "type": record_type,
            "timestamp": timestamp,
            "prediction": prediction
        }, str(record_id))
        return True
    except Exception as e:
        logger.error(f"Error saving Checkup to RAG: {e}")
        return False

def add_interaction_to_db(user_id: str, interaction_id: str, role: str, content: str, timestamp: str) -> bool:
    """Index a chat interaction."""
    try:
        document_text = (
            f"Date: {timestamp}. "
            f"Interaction: {role.upper()}: {content}"
        )
        
        get_vector_store().add(document_text, {
            "user_id": str(user_id),
            "interaction_id": str(interaction_id),
            "type": "chat_log",
            "timestamp": timestamp,
            "role": role
        }, f"chat_{interaction_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving Interaction to RAG: {e}")
        return False

def search_similar_records(user_id: str, query: str, n_results: int = 3) -> List[str]:
    """Retrieve relevant context for a user."""
    try:
        return get_vector_store().search(query, filter_meta={"user_id": str(user_id)}, k=n_results)
    except Exception as e:
        logger.error(f"Error querying RAG: {e}")
        return []

def delete_record_from_db(record_id: str) -> bool:
    """Delete from vector index."""
    return get_vector_store().delete(str(record_id))
