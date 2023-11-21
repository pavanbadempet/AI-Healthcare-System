import sys
import os
import json
# Add root to sys path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models import HealthRecord, User
from backend import rag

def inspect_data():
    session = SessionLocal()
    try:
        # 1. Fetch Users
        users = session.query(User).all()
        print(f"Found {len(users)} users.")
        
        target_user = None
        for u in users:
            print(f"User: {u.username}, ID: {u.id}")
            target_user = u
        
        if not target_user:
            print("No users found.")
            return

        # 2. Fetch Records for last user
        records = session.query(HealthRecord).filter_by(user_id=target_user.id).all()
        print(f"\n--- SQL Records for {target_user.username} ---")
        for r in records:
            print(f"ID: {r.id} | Type: {r.record_type} | Date: {r.timestamp}")
            print(f"Data: {json.dumps(r.data, indent=2)}")
        
        # 3. Test RAG Retrieval
        print(f"\n--- RAG Search Test for 'diabetes' ---")
        docs = rag.search_similar_records("diabetes checkup", n_results=5)
        for i, doc in enumerate(docs):
            print(f"Result {i+1}:")
            print(doc)
            print("-" * 20)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    inspect_data()
