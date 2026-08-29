import httpx
from typing import List, Dict, Any, Tuple
from backend.config import settings
from backend.logger import logger
from backend.schemas import Source

def get_headers():
    return {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Marksheet AI"
    }

def format_context(chunks: List[Dict[str, Any]]) -> str:
    """Formats retrieved chunks into a single context string including document name and page."""
    context_parts = []
    for chunk in chunks:
        doc_name = chunk.get("filename", "marksheet.pdf")
        page = chunk.get("page", "?")
        text = chunk.get("text", "")
        context_parts.append(f"[Document: {doc_name} | Page {page}]\n{text}")
    return "\n\n".join(context_parts)

FALLBACK_MODELS = [
    "nvidia/nemotron-3.5-lightning:free",
    "minimax/minimax-m2.7:free",
    "google/gemma-4-31b-it:free",
    "liquid/lfm-2.5-2.6b:free",
]

def generate_answer(question: str, chunks: List[Dict[str, Any]], chat_history: List[Dict[str, str]] = None) -> Tuple[str, List[Source]]:
    """
    Generate an answer using OpenRouter API based strictly on the provided chunks.
    Automatically tries fallback models if the primary model fails or is rate-limited.
    """
    if not chunks:
        return "I couldn't find that information in the uploaded marksheet(s).", []
        
    context = format_context(chunks)
    
    system_prompt = f"""You are an AI assistant that answers questions about a student's uploaded marksheet(s).
Your ONLY source of truth is the provided marksheet context. You can answer questions about individual marksheets or compare across multiple marksheets if provided.

Rules:
1. Answer only using the provided context.
2. Never invent student information.
3. Never invent marks.
4. Never invent subjects.
5. Never invent CGPA or SGPA.
6. Never assume missing information.
7. If the answer is not present in the provided context, say:
   "I couldn't find that information in the uploaded marksheet(s)."
8. If the question is unrelated to the marksheet, say:
   "I can only answer questions related to the uploaded marksheet(s)."
9. Keep answers concise, factual, and easy to understand. When multiple marksheets are present, clarify which document/semester you are referencing.
10. Do not use external knowledge.
11. Do not silently correct OCR errors.
12. If information is unclear, say it is unclear instead of guessing.

MARKSHEET CONTEXT:
{context}
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    if chat_history:
        messages.extend(chat_history)
        
    messages.append({"role": "user", "content": question})
    
    # Build candidate models list: primary setting first, then fallbacks
    models_to_try = [settings.OPENROUTER_LLM_MODEL]
    for fb in FALLBACK_MODELS:
        if fb not in models_to_try:
            models_to_try.append(fb)
            
    url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
    
    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.0
        }
        
        logger.info(f"Calling LLM: model={model_name}, url={url}")
        
        try:
            with httpx.Client(timeout=45.0) as client:
                response = client.post(url, headers=get_headers(), json=payload)
                if response.status_code == 200:
                    data = response.json()
                    answer = data["choices"][0]["message"]["content"].strip()
                    
                    sources_dict = {}
                    for chunk in chunks:
                        f = chunk.get("filename", "marksheet.pdf")
                        p = chunk.get("page", 1)
                        m = chunk.get("processing_method")
                        key = (f, p)
                        if key not in sources_dict:
                            sources_dict[key] = Source(filename=f, page=p, processing_method=m)
                            
                    sources = list(sources_dict.values())
                    
                    if "I couldn't find that information" in answer or "I can only answer questions related" in answer:
                        sources = []
                        
                    return answer, sources
                else:
                    logger.warning(f"LLM model {model_name} returned status {response.status_code}: {response.text[:200]}")
        except Exception as e:
            logger.warning(f"LLM model {model_name} request error: {e}")
            
    logger.error("All candidate LLM models failed.")
    return "The AI service is temporarily unavailable. Please try again in a moment.", []
