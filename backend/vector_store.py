import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
from backend.config import settings
from backend.logger import logger
import uuid

# Initialize ChromaDB client (persistent)
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)

# Get or create collection
collection_name = "marksheets"
try:
    collection = chroma_client.get_or_create_collection(name=collection_name)
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB collection: {e}")
    raise

def store_chunks(chunks: List[Dict[str, Any]]):
    """
    Store chunks into ChromaDB. ChromaDB will automatically generate embeddings locally.
    """
    if not chunks:
        return
        
    ids = [str(uuid.uuid4()) for _ in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    
    try:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Stored {len(chunks)} chunks in ChromaDB.")
    except Exception as e:
        logger.error(f"Error storing chunks in ChromaDB: {e}")
        raise RuntimeError("Failed to store vector data.")

def delete_document(document_id: str):
    """
    Delete all chunks associated with a specific document_id.
    """
    try:
        collection.delete(where={"document_id": document_id})
        logger.info(f"Deleted document {document_id} from ChromaDB.")
    except Exception as e:
        logger.error(f"Error deleting document {document_id} from ChromaDB: {e}")

def clear_all_documents():
    """
    Clear all documents from ChromaDB collection.
    """
    try:
        col = get_collection()
        # Delete all records
        all_data = col.get()
        if all_data and all_data.get("ids"):
            col.delete(ids=all_data["ids"])
        logger.info("Cleared all documents from ChromaDB.")
    except Exception as e:
        logger.error(f"Error clearing ChromaDB: {e}")

def get_collection():
    return chroma_client.get_or_create_collection(name=collection_name)


