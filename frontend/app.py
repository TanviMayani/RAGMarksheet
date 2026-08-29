import os
import threading
import time
import streamlit as st
import httpx

# API Configuration (supports Streamlit secrets, environment variables, or local fallback)
try:
    API_URL = st.secrets.get("API_URL", os.getenv("API_URL", "http://127.0.0.1:8000"))
except Exception:
    API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Auto-start FastAPI backend in background thread if hosted all-in-one (e.g. Streamlit Community Cloud)
@st.cache_resource
def ensure_backend_running():
    try:
        res = httpx.get(f"{API_URL}/health", timeout=1.0)
        if res.status_code == 200:
            return True
    except Exception:
        pass

    if "127.0.0.1" in API_URL or "localhost" in API_URL:
        try:
            import uvicorn
            from backend.main import app as fastapi_app
            def run_server():
                uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")
            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()
            for _ in range(15):
                try:
                    r = httpx.get(f"{API_URL}/health", timeout=1.0)
                    if r.status_code == 200:
                        return True
                except Exception:
                    time.sleep(0.5)
        except Exception as e:
            print(f"Could not auto-start embedded backend: {e}")
    return False

ensure_backend_running()

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
                    files = {"file": (file.name, file.getvalue(), "application/pdf")}
                    response = httpx.post(f"{API_URL}/upload", files=files, timeout=120.0)
                    
                    if response.status_code == 200:
                        data = response.json()
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
                    else:
                        err_detail = response.json().get("detail", "Error processing file.")
                        st.error(f"❌ {file.name}: {err_detail}")
                except Exception as e:
                    st.error(f"❌ Failed to connect to backend for {file.name}: {e}")
                    
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
            try:
                httpx.post(f"{API_URL}/clear", timeout=10.0)
            except Exception:
                pass
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
                    # Pass the active session document_ids when scope is 'all'
                    if st.session_state.selected_scope == "all":
                        payload = {
                            "document_ids": [doc["document_id"] for doc in st.session_state.documents],
                            "question": prompt,
                            "chat_history": st.session_state.chat_history[:-1]
                        }
                    else:
                        payload = {
                            "document_id": st.session_state.selected_scope,
                            "question": prompt,
                            "chat_history": st.session_state.chat_history[:-1]
                        }
                    res = httpx.post(f"{API_URL}/chat", json=payload, timeout=60.0)
                    
                    if res.status_code == 200:
                        chat_res = res.json()
                        answer = chat_res["answer"]
                        sources = chat_res.get("sources", [])
                        
                        full_response = answer
                        if sources:
                            source_texts = []
                            for s in sources:
                                fname = s.get("filename") or "marksheet.pdf"
                                page = s.get("page", 1)
                                source_texts.append(f"`{fname}` (Page {page})")
                            source_line = "\n\n📄 **Sources:** " + ", ".join(source_texts)
                            full_response += source_line
                            
                        st.markdown(full_response)
                        
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": full_response
                        })
                    else:
                        st.error(f"Failed to get answer from backend: {res.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
else:
    st.info("👈 Please upload your marksheet PDF(s) in the sidebar and click **'Process Marksheets'** to start chatting.")

