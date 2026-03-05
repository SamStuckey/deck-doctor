import numpy as np
import pytest
from unittest.mock import patch
from app.pipeline.ocr import extract_title, crop_title_region

def _make_card_image(h=600, w=450):
    return np.ones((h, w, 3), dtype=np.uint8) * 200

def test_crop_title_region_shape():
    img = _make_card_image(600, 450)
    region = crop_title_region(img)
    assert region.shape[0] < 600 * 0.2
    assert region.shape[1] < 450 * 0.8

def test_extract_title_cleans_whitespace():
    img = _make_card_image()
    with patch("app.pipeline.ocr._run_paddleocr") as mock_ocr:
        mock_ocr.return_value = "  Lightning Bolt  \n"
        result = extract_title(img)
    assert result == "Lightning Bolt"

def test_extract_title_returns_none_on_empty():
    img = _make_card_image()
    with patch("app.pipeline.ocr._run_paddleocr") as mock_ocr:
        mock_ocr.return_value = ""
        result = extract_title(img)
    assert result is None

def test_extract_title_returns_none_on_whitespace_only():
    img = _make_card_image()
    with patch("app.pipeline.ocr._run_paddleocr") as mock_ocr:
        mock_ocr.return_value = "   \n  "
        result = extract_title(img)
    assert result is None
