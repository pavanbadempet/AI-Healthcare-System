import pickle
import os
from backend.rag import DB_FILE

def clean_vector_store():
    if not os.path.exists(DB_FILE):
        print(f"No vector store found at {DB_FILE}")
        return

    print(f"Loading {DB_FILE}...")
    try:
        with open(DB_FILE, 'rb') as f:
            data = pickle.load(f)
    except Exception as e:
        print(f"Error loading pickle: {e}")
        return

    documents = data.get('documents', [])
    metadatas = data.get('metadatas', [])
    vectors = data.get('vectors', [])
    ids = data.get('ids', [])

    initial_count = len(ids)
    print(f"Initial Records: {initial_count}")

    new_documents = []
    new_metadatas = []
    new_vectors = []
    new_ids = []

    deleted_count = 0

    for i in range(len(ids)):
        meta = metadatas[i]
        # CHECK FOR VALID USER_ID
        if meta and 'user_id' in meta and meta['user_id']:
            new_documents.append(documents[i])
            new_metadatas.append(meta)
            new_vectors.append(vectors[i])
            new_ids.append(ids[i])
        else:
            deleted_count += 1
            # print(f"Deleting Orphan Record ID: {ids[i]}")

    if deleted_count > 0:
        print(f"Found {deleted_count} orphan records (missing user_id). Purging...")
        
        # Save back
        with open(DB_FILE, 'wb') as f:
            pickle.dump({
                'documents': new_documents,
                'metadatas': new_metadatas,
                'vectors': new_vectors,
                'ids': new_ids
            }, f)
        print("Vector Store Cleaned and Saved successfully.")
    else:
        print("Vector Store is already clean. No orphans found.")

    print(f"Final Records: {len(new_ids)}")

if __name__ == "__main__":
    clean_vector_store()
