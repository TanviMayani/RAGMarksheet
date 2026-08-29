# Marksheet AI Assistant

This is a complete Retrieval-Augmented Generation (RAG) application that allows you to upload a marksheet PDF and chat with it.

## Features
- **PDF Processing**: Supports Digital, Scanned, and Mixed PDFs using PyMuPDF and Tesseract OCR.
- **RAG Architecture**: Uses character-based chunking, embeddings via OpenRouter, and ChromaDB for vector storage.
- **Hallucination Protection**: Strict prompting ensures the AI only uses data found in your marksheet.
- **Document Isolation**: Unique document IDs ensure you only query the document you uploaded.

## Installation

### Prerequisites
1. **Python 3.11+**
2. **Tesseract OCR**: You must install Tesseract separately on your system. 
   - Windows: Download from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)

### Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables
Copy `.env.example` to `.env` and fill in your OpenRouter API key and desired models.
If Tesseract is not in your system PATH, update `TESSERACT_CMD` in `.env` (e.g., `TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe`).

## Running the Application

### Backend (FastAPI)
```bash
uvicorn backend.main:app --reload
```
API Documentation will be at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Frontend (Streamlit)
Open a new terminal, activate the venv, and run:
```bash
streamlit run frontend/app.py
```

## Testing
Run tests using:
```bash
pytest tests/
```

## Free Deployment 🚀
For a complete guide to deploying this app freely on **Streamlit Community Cloud**, **Hugging Face Spaces (16GB RAM)**, or **Render**, see [DEPLOYMENT.md](file:///d:/RAGMarksheet/DEPLOYMENT.md).
