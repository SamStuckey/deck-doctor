import numpy as np
import cv2
from typing import Optional

_paddle_ocr = None

def _get_ocr():
    global _paddle_ocr
    if _paddle_ocr is None:
        from paddleocr import PaddleOCR
        _paddle_ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    return _paddle_ocr

def crop_title_region(img: np.ndarray) -> np.ndarray:
    """
    Crop the title region from a card image.
    MTG card titles are in the top ~12% of the card, left ~72% of width
    (the right portion is the mana cost symbols).
    """
    h, w = img.shape[:2]
    y2 = int(h * 0.12)
    x2 = int(w * 0.72)
    return img[0:y2, 0:x2]

def _preprocess(img: np.ndarray) -> np.ndarray:
    """Enhance contrast for OCR accuracy."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    enhanced = clahe.apply(gray)
    h, w = enhanced.shape[:2]
    if h < 40:
        scale = 40 / h
        enhanced = cv2.resize(enhanced, (int(w * scale), 40), interpolation=cv2.INTER_CUBIC)
    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

def _run_paddleocr(img: np.ndarray) -> str:
    """Run PaddleOCR and return concatenated text."""
    ocr = _get_ocr()
    result = ocr.ocr(img, cls=True)
    if not result or not result[0]:
        return ""
    texts = [line[1][0] for line in result[0] if line and line[1]]
    return " ".join(texts)

def extract_title(card_img: np.ndarray) -> Optional[str]:
    """
    Extract the card title from a card image.
    Crops the title region, preprocesses, runs PaddleOCR.
    Returns cleaned title string, or None if nothing found.
    """
    region = crop_title_region(card_img)
    processed = _preprocess(region)
    raw = _run_paddleocr(processed)
    cleaned = raw.strip()
    return cleaned if cleaned else None
