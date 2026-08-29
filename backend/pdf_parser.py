import fitz  # PyMuPDF
from typing import List, Dict, Any
from backend.ocr import ocr_image, is_ocr_available
from backend.logger import logger
from PIL import Image
import io

def has_meaningful_text(text: str) -> bool:
    """
    Determine if the extracted text is meaningful.
    We check for alphanumeric density.
    """
    if not text:
        return False
    
    alnum_count = sum(c.isalnum() for c in text)
    if len(text) == 0:
        return False
        
    # If less than 10 alphanumeric characters, it's likely just noise/scanned
    if alnum_count < 10:
        return False
        
    return True

def clean_text(text: str) -> str:
    """
    Clean basic extraction noise while preserving structure.
    """
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    return '\n'.join(cleaned_lines)

def process_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Process a PDF file page by page. Uses text extraction first.
    If text is not meaningful, falls back to OCR if available.
    """
    pages_data = []
    
    try:
        doc = fitz.open(file_path)
        logger.info(f"Processing PDF: {file_path}, Pages: {len(doc)}")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            cleaned_text = clean_text(text)
            
            if has_meaningful_text(cleaned_text):
                logger.info(f"Page {page_num + 1}: Found meaningful text via PyMuPDF.")
                pages_data.append({
                    "page": page_num + 1,
                    "text": cleaned_text,
                    "method": "text"
                })
            else:
                logger.info(f"Page {page_num + 1}: Little/no text found. Falling back to OCR.")
                if not is_ocr_available():
                    logger.error("OCR is required for this page but not available.")
                    raise RuntimeError("This marksheet requires OCR, but OCR is not available on this system. Please install Tesseract OCR.")
                
                # Render page to image at ~300 DPI for OCR
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                ocr_text = ocr_image(img)
                cleaned_ocr_text = clean_text(ocr_text)
                
                pages_data.append({
                    "page": page_num + 1,
                    "text": cleaned_ocr_text,
                    "method": "ocr"
                })
                
        doc.close()
        return pages_data
        
    except Exception as e:
        logger.error(f"Error processing PDF {file_path}: {e}")
        raise e
