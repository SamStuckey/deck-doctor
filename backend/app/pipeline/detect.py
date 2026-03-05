from dataclasses import dataclass
import numpy as np
import cv2
from typing import Optional

@dataclass
class CardRegion:
    crop: np.ndarray
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2

def _opencv_detect(img: np.ndarray) -> list[CardRegion]:
    """Fallback: find card-shaped rectangles via contour detection."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    regions = []
    ih, iw = img.shape[:2]
    min_area = (iw * ih) * 0.02  # ignore tiny blobs

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        # MTG cards are ~2.5" x 3.5" — aspect ratio ~0.7
        aspect = w / h if h > 0 else 0
        if 0.5 < aspect < 0.9:
            pad = 4
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(iw, x + w + pad)
            y2 = min(ih, y + h + pad)
            regions.append(CardRegion(crop=img[y1:y2, x1:x2], bbox=(x1, y1, x2, y2)))

    return regions

def detect_cards(
    img: np.ndarray,
    fallback_to_full_image: bool = True,
    use_yolo: bool = True,
) -> list[CardRegion]:
    """
    Detect MTG card regions in an image.
    Tries YOLOv8 first, falls back to OpenCV contour detection,
    then falls back to full image if fallback_to_full_image=True.
    """
    regions: list[CardRegion] = []

    if use_yolo:
        try:
            from ultralytics import YOLO
            model = YOLO("yolov8n.pt")  # downloaded on first run (~6MB)
            results = model(img, verbose=False)
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                crop = img[y1:y2, x1:x2]
                if crop.size > 0:
                    regions.append(CardRegion(crop=crop, bbox=(x1, y1, x2, y2)))
        except Exception:
            regions = []

    if not regions:
        regions = _opencv_detect(img)

    if not regions and fallback_to_full_image:
        h, w = img.shape[:2]
        regions = [CardRegion(crop=img.copy(), bbox=(0, 0, w, h))]

    return regions
