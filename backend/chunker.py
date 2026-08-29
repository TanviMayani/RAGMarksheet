from typing import List, Dict, Any
from backend.config import settings

def chunk_pages(pages_data: List[Dict[str, Any]], document_id: str, filename: str = "") -> List[Dict[str, Any]]:
    """
    Chunks text from pages while preserving metadata (document_id, filename, page, method).
    Simple character overlap chunking strategy.
    """
    chunk_size = settings.CHUNK_SIZE
    chunk_overlap = settings.CHUNK_OVERLAP
    chunks = []
    
    for page in pages_data:
        text = page.get("text", "")
        page_num = page.get("page")
        method = page.get("method")
        
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            # If not at the end of text, try to find a natural break (newline or space)
            if end < text_length:
                # Try to break at a newline to keep subjects/marks together
                last_newline = text.rfind('\n', start, end)
                if last_newline != -1 and last_newline > start + chunk_size // 2:
                    end = last_newline
                else:
                    # Fallback to space
                    last_space = text.rfind(' ', start, end)
                    if last_space != -1 and last_space > start + chunk_size // 2:
                        end = last_space
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "document_id": document_id,
                        "filename": filename or "marksheet.pdf",
                        "page": page_num,
                        "processing_method": method,
                        "document_type": "marksheet"
                    }
                })
            
            # Advance start pointer, accounting for overlap
            start = end - chunk_overlap if end < text_length else text_length
            
    return chunks
