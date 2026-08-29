import os
import sys
from pathlib import Path
import uuid
import tempfile

# Add project root directory to sys.path so 'backend' is importable anywhere
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import httpx

# Sync Streamlit secrets to os.environ so all backend modules can access them
try:
    if hasattr(st, "secrets"):
        for k, v in st.secrets.items():
            if isinstance(v, str) and k not in os.environ:
                os.environ[k] = v
except Exception:
    pass

# Import backend services directly for robust, zero-latency in-memory execution
from backend.pdf_parser import process_pdf
from backend.validator import is_marksheet
from backend.chunker import chunk_pages
from backend.vector_store import store_chunks, clear_all_documents
from backend.retriever import retrieve_relevant_chunks
from backend.llm import generate_answer

# Check if an external remote API URL is specified
API_URL = os.getenv("API_URL", "")
IS_REMOTE_API = API_URL.startswith("http://") or API_URL.startswith("https://")
if IS_REMOTE_API and ("127.0.0.1" in API_URL or "localhost" in API_URL):
    IS_REMOTE_API = False

# Backend service helper wrappers (Supports both direct in-memory and remote API)
def handle_upload(file):
    if IS_REMOTE_API:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        response = httpx.post(f"{API_URL}/upload", files=files, timeout=120.0)
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Error processing file.")
            return {"success": False, "message": detail}
    
    # In-memory direct execution
    if not file.name.lower().endswith(".pdf"):
        return {"success": False, "message": "Please upload a valid PDF file."}
        
    doc_id = str(uuid.uuid4())
    os.makedirs("uploads", exist_ok=True)
    temp_path = os.path.join("uploads", f"{doc_id}_{file.name}")
    
    try:
        with open(temp_path, "wb") as f:
            f.write(file.getvalue())
            
        pages_data = process_pdf(temp_path)
        if not pages_data:
            return {"success": False, "message": "Unable to extract readable text from this marksheet."}
            
        if not is_marksheet(pages_data):
            return {"success": False, "message": "The uploaded document does not appear to be a marksheet."}
            
        chunks = chunk_pages(pages_data, doc_id, filename=file.name)
        if not chunks:
            return {"success": False, "message": "Unable to process marksheet chunks. Please try again."}
            
        store_chunks(chunks)
        
        methods = {p.get("method", "text") for p in pages_data}
        overall_method = "Mixed Text + OCR" if len(methods) > 1 else ("Text" if "text" in methods else "OCR")
        
        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.name,
            "pages": len(pages_data),
            "processing_method": overall_method
        }
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

def handle_chat(question, document_id=None, document_ids=None, chat_history=None):
    if IS_REMOTE_API:
        payload = {
            "question": question,
            "document_id": document_id,
            "document_ids": document_ids,
            "chat_history": chat_history or []
        }
        res = httpx.post(f"{API_URL}/chat", json=payload, timeout=60.0)
        if res.status_code == 200:
            return res.json()
        else:
            return {"answer": f"Error from backend: {res.text}", "sources": []}
            
    # In-memory direct execution
    chunks = retrieve_relevant_chunks(
        question=question,
        document_id=document_id,
        document_ids=document_ids
    )
    answer, sources = generate_answer(question, chunks, chat_history or [])
    serialized_sources = [
        {"filename": s.filename, "page": s.page, "processing_method": s.processing_method}
        if hasattr(s, "filename") else s
        for s in sources
    ]
    return {"answer": answer, "sources": serialized_sources}

def handle_clear():
    if IS_REMOTE_API:
        try:
            httpx.post(f"{API_URL}/clear", timeout=10.0)
        except Exception:
            pass
    else:
        clear_all_documents()

# ----------------- Streamlit UI -----------------
st.set_page_config(page_title="Marksheet AI Assistant", page_icon="🎓", layout="wide")

st.title("🎓 Marksheet AI Assistant")

# Initialize session state
if "documents" not in st.session_state:
    st.session_state.documents = []  # list of {"document_id": str, "filename": str, "pages": int, "method": str}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_scope" not in st.session_state:
    st.session_state.selected_scope = "all"

# Sidebar for Document Management
with st.sidebar:
    st.header("📁 Upload Marksheets")
    uploaded_files = st.file_uploader(
        "Choose one or more marksheet PDFs", 
        type=["pdf"], 
        accept_multiple_files=True,
        help="Upload multiple semester marksheets to query or compare them."
    )
    
    if st.button("⚡ Process Marksheets", use_container_width=True) and uploaded_files:
        with st.status("Processing uploaded marksheets...", expanded=True) as status:
            for file in uploaded_files:
                # Check if already processed
                existing_names = [d["filename"] for d in st.session_state.documents]
                if file.name in existing_names:
                    st.write(f"ℹ️ **{file.name}** is already processed.")
                    continue
                    
                st.write(f"Processing **{file.name}**...")
                try:
                    data = handle_upload(file)
                    if data.get("success"):
                        st.session_state.documents.append({
                            "document_id": data["document_id"],
                            "filename": data.get("filename") or file.name,
                            "pages": data["pages"],
                            "method": data["processing_method"]
                        })
                        st.write(f"✅ **{file.name}** processed successfully!")
                    else:
                        st.error(f"❌ {file.name}: {data.get('message', 'Validation failed.')}")
                except Exception as e:
                    st.error(f"❌ Failed to process {file.name}: {e}")
                    
            status.update(label="Processing Finished!", state="complete", expanded=False)
            
    st.markdown("---")
    
    # Uploaded Documents List
    if st.session_state.documents:
        st.subheader(f"📚 Uploaded ({len(st.session_state.documents)})")
        for doc in st.session_state.documents:
            with st.container():
                st.markdown(f"**📄 {doc['filename']}**")
                st.caption(f"Pages: {doc['pages']} | Method: {doc['method']}")
                
        if st.button("🗑️ Clear All Marksheets", use_container_width=True):
            handle_clear()
            st.session_state.documents = []
            st.session_state.chat_history = []
            st.session_state.selected_scope = "all"
            st.rerun()
    else:
        st.info("No marksheets uploaded yet. Upload one or more PDFs above to begin.")

# Main Chat Interface
if st.session_state.documents:
    # Scope Selector
    scope_options = {"all": f"🌐 All Marksheets ({len(st.session_state.documents)} documents)"}
    for doc in st.session_state.documents:
        scope_options[doc["document_id"]] = f"📄 {doc['filename']}"
        
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_key = st.selectbox(
            "🎯 Query Scope:",
            options=list(scope_options.keys()),
            format_func=lambda k: scope_options[k],
            index=0 if st.session_state.selected_scope not in scope_options else list(scope_options.keys()).index(st.session_state.selected_scope)
        )
        st.session_state.selected_scope = selected_key
        
    with col2:
        if st.button("🧹 Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    # Suggested Prompts
    with st.expander("💡 Suggested Questions"):
        if selected_key == "all" and len(st.session_state.documents) > 1:
            st.markdown("""
            - Compare my highest marks across all uploaded semesters.
            - What is my average percentage/SGPA across each semester?
            - In which semester did I score the highest in Mathematics?
            - List all subjects and marks from all uploaded marksheets.
            """)
        else:
            st.markdown("""
            - What is my CGPA / SGPA?
            - Which subject has the highest marks?
            - Which subject has the lowest marks?
            - What are my marks in [Subject Name]?
            - What is my total score and percentage?
            """)

    st.markdown("---")

    # Display Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ask a question about your marksheet(s)..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Analyzing marksheet data..."):
                try:
                    if st.session_state.selected_scope == "all":
                        chat_res = handle_chat(
                            question=prompt,
                            document_ids=[doc["document_id"] for doc in st.session_state.documents],
                            chat_history=st.session_state.chat_history[:-1]
                        )
                    else:
                        chat_res = handle_chat(
                            question=prompt,
                            document_id=st.session_state.selected_scope,
                            chat_history=st.session_state.chat_history[:-1]
                        )
                    
                    answer = chat_res.get("answer", "")
                    sources = chat_res.get("sources", [])
                    
                    full_response = answer
                    if sources:
                        source_texts = []
                        for s in sources:
                            fname = getattr(s, "filename", None) or (s.get("filename") if isinstance(s, dict) else "marksheet.pdf")
                            page = getattr(s, "page", None) or (s.get("page", 1) if isinstance(s, dict) else 1)
                            source_texts.append(f"`{fname}` (Page {page})")
                        source_line = "\n\n📄 **Sources:** " + ", ".join(source_texts)
                        full_response += source_line
                        
                    st.markdown(full_response)
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": full_response
                    })
                except Exception as e:
                    st.error(f"Error generating answer: {e}")
else:
    st.info("👈 Please upload your marksheet PDF(s) in the sidebar and click **'Process Marksheets'** to start chatting.")
