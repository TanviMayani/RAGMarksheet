import httpx
from typing import List
from backend.config import settings
from backend.logger import logger

def get_headers():
    return {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Marksheet AI"
    }

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using OpenRouter API.
    """
    if not texts:
        return []
        
    url = f"{settings.OPENROUTER_BASE_URL}/embeddings"
    payload = {
        "model": settings.OPENROUTER_EMBEDDING_MODEL,
        "input": texts
    }
    
    try:
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(url, headers=get_headers(), json=payload)
                    response.raise_for_status()
                    data = response.json()
                    
                    embeddings = [item["embedding"] for item in data["data"]]
                    return embeddings
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                logger.error(f"Embeddings HTTP error (attempt {attempt + 1}/{max_retries}): {status}")
                
                if status == 429 and attempt < max_retries - 1:
                    import time
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited on embeddings. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                raise
                
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise RuntimeError("Unable to generate embeddings right now.")

def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text.
    """
    embeddings = generate_embeddings([text])
    if embeddings:
        return embeddings[0]
    return []
