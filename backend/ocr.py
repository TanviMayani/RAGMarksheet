import numpy as np
from PIL import Image
from backend.config import settings
from backend.logger import logger

_ocr_engine = None
_ocr_initialized = False

def get_ocr_engine():
    global _ocr_engine, _ocr_initialized
    if not _ocr_initialized:
        _ocr_initialized = True
        try:
            from rapidocr_onnxruntime import RapidOCR
            _ocr_engine = RapidOCR()
            logger.info("RapidOCR initialized successfully.")
        except Exception as e:
            logger.warning(f"RapidOCR could not be loaded: {e}. Scanned image OCR will be disabled, text-based PDFs will work normally.")
            _ocr_engine = None
    return _ocr_engine

def is_ocr_available() -> bool:
    if not settings.OCR_ENABLED:
        return False
    return get_ocr_engine() is not None

def ocr_image(image: Image.Image) -> str:
    """
    Extract text from a PIL Image using RapidOCR (ONNX Runtime).
    """
    if not settings.OCR_ENABLED:
        logger.warning("OCR is disabled in settings.")
        return ""
        
    engine = get_ocr_engine()
    if engine is None:
        logger.warning("OCR engine is not available.")
        return ""
        
    try:
        if image.mode != "RGB":
            image = image.convert("RGB")
        img_np = np.array(image)
        
        result, _ = engine(img_np)
        
        if result:
            texts = [line[1] for line in result]
            return "\n".join(texts)
        return ""
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        return ""
