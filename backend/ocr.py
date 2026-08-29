import numpy as np
from PIL import Image
from backend.config import settings
from backend.logger import logger
from rapidocr_onnxruntime import RapidOCR

ocr_engine = RapidOCR()

def is_ocr_available() -> bool:
    return True

def ocr_image(image: Image.Image) -> str:
    """
    Extract text from a PIL Image using RapidOCR (ONNX Runtime).
    """
    if not settings.OCR_ENABLED:
        logger.warning("OCR is disabled in settings.")
        return ""
        
    try:
        # Convert PIL Image to RGB and then to numpy array for RapidOCR
        if image.mode != "RGB":
            image = image.convert("RGB")
        img_np = np.array(image)
        
        result, _ = ocr_engine(img_np)
        
        if result:
            # result is a list of tuples: [([[...box...]], 'text', confidence), ...]
            texts = [line[1] for line in result]
            return "\n".join(texts)
        return ""
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""
