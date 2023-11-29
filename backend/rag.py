
import os
import json
import pickle
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DB_FILE = "vector_store.pkl"

# Global lazy loader
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading Embedding Model (Lazy)...")
        _embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embedding_model

class SimpleVectorStore:
    def __init__(self):
        self.documents = [] 
        self.metadatas = [] 
        self.vectors = []   
        self.ids = []       
        self.load()

    def load(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents', [])
                    self.metadatas = data.get('metadatas', [])
                    self.vectors = data.get('vectors', [])
                    self.ids = data.get('ids', [])
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")

    def save(self):
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

    def add(self, text, metadata, record_id):
        model = get_embedding_model()
        vector = model.embed_query(text)
        
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

    def delete(self, record_id):
        if record_id in self.ids:
            idx = self.ids.index(record_id)
            self.documents.pop(idx)
            self.metadatas.pop(idx)
            self.vectors.pop(idx)
            self.ids.pop(idx)
            self.save()
            return True
        return False

    def search(self, query, filter_meta=None, k=3):
        if not self.vectors:
            return []
        
        # 1. Filter indices FIRST (Optimization: Reduce search space)
        # Note: Since this is simple list-based, we'll search all then filter results, 
        # or filter indices then embed. Embedding is the bottleneck if caching isn't perfect,
        # but here we already have vectors. 
        # Better: Compute all similarities, then filter top results.
        
        model = get_embedding_model()
        query_vector = model.embed_query(query)
        
        vec_matrix = np.array(self.vectors)
        q_vec = np.array([query_vector])
        
        sim_scores = cosine_similarity(q_vec, vec_matrix)[0]
        # Get sort indices (descending)
        sorted_indices = sim_scores.argsort()[::-1]
        
        results = []
        count = 0
        
        for idx in sorted_indices:
            if sim_scores[idx] <= 0.0: break # No more relevance
            
            # Metadata Filter Check
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

store = SimpleVectorStore()

def add_checkup_to_db(user_id: str, record_id: str, record_type: str, data: dict, prediction: str, timestamp: str):
    try:
        # Use simple string representation
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
        logger.error(f"Error saving to SimpleStore: {e}")
        return False

def add_interaction_to_db(user_id: str, interaction_id: str, role: str, content: str, timestamp: str):
    """
    Index a chat interaction (User or Assistant).
    """
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
        logger.error(f"Error saving interaction to SimpleStore: {e}")
        return False

def search_similar_records(user_id: str, query: str, n_results: int = 3):
    try:
        return store.search(query, filter_meta={"user_id": str(user_id)}, k=n_results)
    except Exception as e:
        logger.error(f"Error querying SimpleStore: {e}")
        return []

def delete_record_from_db(record_id: str):
    return store.delete(str(record_id))
