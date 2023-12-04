
import os
import json
import pickle
import numpy as np
import logging
from typing import List, Dict, Optional, Any, Union
from langchain_huggingface import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

# --- Logging Configuration ---
# logging.basicConfig(level=logging.INFO) # Handled in main.py
logger = logging.getLogger(__name__)

# --- Constants ---
DB_FILE = os.path.join(os.path.dirname(__file__), "..", "models", "vector_store.pkl")
MODEL_NAME = "all-MiniLM-L6-v2"

# --- Global Lazy Loader ---
_embedding_model = None

def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Lazy loads the HuggingFace Embedding Model.
    Singleton pattern to avoid re-loading model on every request.
    """
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading Embedding Model: {MODEL_NAME}...")
        _embedding_model = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    return _embedding_model

class SimpleVectorStore:
    """
    A persistent, file-based vector store using Pickle and Scikit-Learn.
    mimics behavior of ChromaDB but without external dependencies.
    """
    
    def __init__(self):
        """Initialize and load existing store if available."""
        self.documents: List[str] = [] 
        self.metadatas: List[Dict[str, Any]] = [] 
        self.vectors: List[List[float]] = []   
        self.ids: List[str] = []       
        self.load()

    def load(self) -> None:
        """Load vector store data from pickle file."""
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
        """Persist vector store data to pickle file."""
        try:
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
        """
        Add or Update a document in the store.
        
        Args:
            text (str): Content to embed.
            metadata (dict): Metadata for filtering (e.g. user_id).
            record_id (str): Unique ID.
        """
        model = get_embedding_model()
        vector = model.embed_query(text)
        
        if record_id in self.ids:
            idx = self.ids.index(record_id)
            self.documents[idx] = text
            self.metadatas[idx] = metadata
            self.vectors[idx] = vector
            logger.debug(f"Updated record {record_id}")
        else:
            self.documents.append(text)
            self.metadatas.append(metadata)
            self.vectors.append(vector)
            self.ids.append(record_id)
            logger.debug(f"Added record {record_id}")
        
        self.save()

    def delete(self, record_id: str) -> bool:
        """Delete a document by ID."""
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
        """
        Semantic search for relevant documents.
        
        Args:
            query (str): The search query.
            filter_meta (dict): Key-value pairs to filter results (e.g. {"user_id": "1"}).
            k (int): Number of Top-K results to return.
            
        Returns:
            List[str]: List of matching document texts.
        """
        if not self.vectors:
            return []
        
        # Embed query
        model = get_embedding_model()
        query_vector = model.embed_query(query)
        
        vec_matrix = np.array(self.vectors)
        q_vec = np.array([query_vector])
        
        # Compute Cosine Similarity
        sim_scores = cosine_similarity(q_vec, vec_matrix)[0]
        # Get indices sorted by score descending
        sorted_indices = sim_scores.argsort()[::-1]
        
        results = []
        count = 0
        
        for idx in sorted_indices:
            if sim_scores[idx] <= 0.0: break # Threshold
            
            # Apply Metadata Filter
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

# Singleton Instance
store = SimpleVectorStore()

# --- Public Interface Functions ---

def add_checkup_to_db(user_id: str, record_id: str, record_type: str, data: dict, prediction: str, timestamp: str) -> bool:
    """Format and index a health checkup record."""
    try:
        data_str = ", ".join([f"{k}: {v}" for k,v in data.items()])
        document_text = (
            f"User: {user_id}\n"
            f"Date: {timestamp}\n"
            f"Checkup Type: {record_type}\n"
            f"Result: {prediction}\n"
            f"Clinical Data: {data_str}"
        )
        
        store.add(document_text, {
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
    """Index a chat interaction for memory."""
    try:
        document_text = (
            f"Date: {timestamp}. "
            f"Interaction: {role.upper()}: {content}"
        )
        
        store.add(document_text, {
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
    """Retrieve relevant context for a user query."""
    try:
        return store.search(query, filter_meta={"user_id": str(user_id)}, k=n_results)
    except Exception as e:
        logger.error(f"Error querying RAG: {e}")
        return []

def delete_record_from_db(record_id: str) -> bool:
    """Remove a record from the vector index."""
    return store.delete(str(record_id))
