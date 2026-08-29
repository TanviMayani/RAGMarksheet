import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas import UploadResponse, ChatRequest, ChatResponse
from backend.config import settings
from backend.logger import logger

from backend.pdf_parser import process_pdf
from backend.validator import is_marksheet
from backend.chunker import chunk_pages
from backend.vector_store import store_chunks, clear_all_documents, delete_document
from backend.retriever import retrieve_relevant_chunks
from backend.llm import generate_answer

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY is not set.")
    if not settings.OPENROUTER_LLM_MODEL:
        logger.warning("OPENROUTER_LLM_MODEL is not set. Chat will fail.")
    else:
        logger.info(f"Using LLM model: {settings.OPENROUTER_LLM_MODEL}")
    yield

app = FastAPI(title="Marksheet AI Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    # 1. Validation
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a valid PDF file.")
        
    file.file.seek(0, 2)
    file_size_mb = file.file.tell() / (1024 * 1024)
    file.file.seek(0)
    
    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail="The PDF is too large. Please upload a smaller marksheet.")
        
    document_id = str(uuid.uuid4())
    temp_path = f"uploads/{document_id}.pdf"
    
    try:
        # Save temp file
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
            
        logger.info(f"Saved temp PDF: {temp_path}")
        
        # 2. Extract
        try:
            pages_data = process_pdf(temp_path)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            raise HTTPException(status_code=400, detail="Unable to read this PDF. Please upload a valid marksheet.")
            
        if not pages_data:
            raise HTTPException(status_code=400, detail="Unable to extract readable text from this marksheet.")
            
        # 3. Validate marksheet
        if not is_marksheet(pages_data):
            # It's not a marksheet
            return UploadResponse(
                success=False,
                document_id=None,
                message="The uploaded document does not appear to be a marksheet.",
                pages=0,
                processing_method=None
            )
            
        # 4. Chunk
        chunks = chunk_pages(pages_data, document_id, filename=file.filename)
        if not chunks:
            raise HTTPException(status_code=500, detail="Unable to process the marksheet right now. Please try again.")
            
        # 5. Store (Embeddings generated automatically by ChromaDB)
        try:
            store_chunks(chunks)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Unable to process the marksheet right now. Please try again.")
            
        # Determine overall processing method
        methods = {p["method"] for p in pages_data}
        overall_method = "Mixed Text + OCR" if len(methods) > 1 else ("Text" if "text" in methods else "OCR")
        
        return UploadResponse(
            success=True,
            document_id=document_id,
            filename=file.filename,
            message="Marksheet processed successfully.",
            pages=len(pages_data),
            processing_method=overall_method
        )
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            logger.info(f"Deleted temp PDF: {temp_path}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # 1. Retrieve
    chunks = retrieve_relevant_chunks(
        question=request.question,
        document_id=request.document_id,
        document_ids=request.document_ids
    )
    
    # 2. Generate
    answer, sources = generate_answer(request.question, chunks, request.chat_history)
    
    return ChatResponse(
        answer=answer,
        sources=sources
    )

@app.post("/clear")
def clear_documents():
    clear_all_documents()
    return {"message": "All documents cleared successfully."}


