from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_invalid_file_type():
    # Attempt to upload a non-PDF file
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")}
    )
    assert response.status_code == 400
    assert "valid PDF" in response.json()["detail"]

# More comprehensive tests for PDF processing, RAG, and document isolation
# would typically require mocking PyMuPDF, OpenRouter, and ChromaDB.
# A basic isolation test mock:

def test_document_isolation_mock():
    # In a real environment, we would insert mock chunks into ChromaDB 
    # with different document_ids and ensure /chat endpoint strictly filters by document_id.
    pass
