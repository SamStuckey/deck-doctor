import numpy as np
import pytest
from app.pipeline.detect import detect_cards, CardRegion

def _make_white_image(h=600, w=450):
    return np.ones((h, w, 3), dtype=np.uint8) * 255

def test_detect_returns_list():
    img = _make_white_image()
    result = detect_cards(img, use_yolo=False)
    assert isinstance(result, list)

def test_card_region_has_crop():
    img = _make_white_image()
    region = CardRegion(crop=img[0:400, 0:300], bbox=(0, 0, 300, 400))
    assert region.crop.shape == (400, 300, 3)
    assert region.bbox == (0, 0, 300, 400)

def test_full_image_fallback_when_no_detection():
    """If no cards detected, return the whole image as one region."""
    img = _make_white_image(100, 100)
    result = detect_cards(img, fallback_to_full_image=True, use_yolo=False)
    assert len(result) == 1
    assert result[0].crop.shape == img.shape

def test_no_fallback_returns_empty():
    """If no cards detected and fallback disabled, return empty list."""
    img = _make_white_image(100, 100)
    result = detect_cards(img, fallback_to_full_image=False, use_yolo=False)
    assert isinstance(result, list)
