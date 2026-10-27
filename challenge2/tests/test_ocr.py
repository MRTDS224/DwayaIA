import pytest
from PIL import Image
from challenge2.vision.ocr_engine import ocr_engine


def test_arabic_detection():
    assert ocr_engine.is_arabic("دوليبران 1000 مغ") is True
    assert ocr_engine.is_arabic("DOLIPRANE 1000 MG") is False
    assert ocr_engine.is_arabic("Paracetamol باراسيتامول") is True


def test_format_bidi_arabic():
    # Avec tashkeel
    tashkeel_text = "دُولِيبْرَانْ"
    cleaned = ocr_engine.format_bidi_arabic(tashkeel_text)
    assert "َ" not in cleaned
    assert "ُ" not in cleaned
    assert "ْ" not in cleaned


def test_dosage_and_units_extraction():
    dummy_img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    hints = ["DOLIPRANE", "1000 mg", "boîte de 8 comprimés", "باراسيتامول"]
    res = ocr_engine.extract_text(dummy_img, hint_tokens=hints)

    assert "DOLIPRANE" in res["text_fr"]
    assert "باراسيتامول" in res["text_ar"]
    assert len(res["all_tokens"]) >= 3
    assert any("1000" in d for d in res["detected_dosages"])
    assert res["conf_ocr"] >= 0.80

