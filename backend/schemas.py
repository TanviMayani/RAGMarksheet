from pydantic import BaseModel
from typing import Optional, List, Dict

class UploadResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    filename: Optional[str] = None
    message: str
    pages: Optional[int] = None
    processing_method: Optional[str] = None

class ChatRequest(BaseModel):
    document_id: Optional[str] = None  # None or "all" to query all documents
    document_ids: Optional[List[str]] = None  # Optional explicit list of document IDs
    question: str
    chat_history: Optional[List[Dict[str, str]]] = None

class Source(BaseModel):
    filename: Optional[str] = None
    page: int
    processing_method: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]

