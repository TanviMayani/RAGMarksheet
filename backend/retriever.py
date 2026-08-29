from typing import List, Dict, Any
from backend.config import settings
from backend.vector_store import get_collection
from backend.logger import logger

def retrieve_relevant_chunks(
    question: str, 
    document_id: str = None, 
    document_ids: List[str] = None,
    top_k: int = None
) -> List[Dict[str, Any]]:
    """
    Retrieves the most relevant chunks for a question.
    - If document_id is provided and != "all", filters to that specific document.
    - If document_ids list is provided, filters to those documents using ChromaDB $in.
    - If document_id is "all" or None (and document_ids is None), searches across all uploaded documents.
    """
    if top_k is None:
        top_k = settings.TOP_K if document_id and document_id != "all" else settings.TOP_K * 2
        
    try:
        where_filter = None
        if document_ids and len(document_ids) == 1:
            where_filter = {"document_id": document_ids[0]}
        elif document_ids and len(document_ids) > 1:
            where_filter = {"document_id": {"$in": document_ids}}
        elif document_id and document_id != "all":
            where_filter = {"document_id": document_id}
            
        query_kwargs = {
            "query_texts": [question],
            "n_results": top_k
        }
        if where_filter:
            query_kwargs["where"] = where_filter
            
        col = get_collection()
        results = col.query(**query_kwargs)

        
        retrieved = []
        if not results["documents"] or not results["documents"][0]:
            return []
            
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0]*len(documents)
        
        for doc, meta, dist in zip(documents, metadatas, distances):
            logger.info(f"Retrieved chunk with distance: {dist}")
            
            # Reject only obvious outliers (distance > 2.0)
            MAX_DISTANCE = 2.0
            if dist > MAX_DISTANCE:
                logger.warning(f"Dropping chunk with distance {dist:.4f} (exceeds threshold {MAX_DISTANCE})")
                continue
                
            retrieved.append({
                "text": doc,
                "page": meta.get("page", 0),
                "document_id": meta.get("document_id"),
                "filename": meta.get("filename", "marksheet.pdf"),
                "processing_method": meta.get("processing_method")
            })
            
        return retrieved
        
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return []
