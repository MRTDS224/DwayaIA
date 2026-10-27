import io
import pytest
from PIL import Image, ImageDraw
import numpy as np

from challenge2.vision.preprocessor import preprocessor, ImagePreprocessor


@pytest.fixture
def sample_medicine_image():
    """Crée une image synthétique simulant une boîte de médicament avec texte."""
    img = Image.new("RGB", (600, 400), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    # Rectangle représentant la boîte
    draw.rectangle([60, 40, 540, 360], fill=(255, 255, 255), outline=(13, 148, 136), width=4)
    # Bandes de couleur et texte simulé
    draw.rectangle([80, 60, 520, 140], fill=(37, 99, 235))
    draw.rectangle([80, 160, 350, 220], fill=(220, 38, 38))
    draw.rectangle([80, 250, 480, 300], fill=(50, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_load_image(sample_medicine_image):
    img = preprocessor.load_image(sample_medicine_image)
    assert isinstance(img, Image.Image)
    assert img.size[0] <= 1200
    assert img.size[1] <= 1200


def test_apply_clahe(sample_medicine_image):
    img = preprocessor.load_image(sample_medicine_image)
    clahe_img = preprocessor.apply_clahe(img)
    assert isinstance(clahe_img, Image.Image)
    assert clahe_img.size == img.size


def test_estimate_skew_and_deskew():
    # Créer une image légèrement inclinée
    img = Image.new("RGB", (300, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    for y in range(40, 160, 20):
        draw.line([(30, y), (270, y)], fill=(0, 0, 0), width=3)

    rotated = img.rotate(15, expand=True, fillcolor=(255, 255, 255))
    angle = preprocessor.estimate_skew_angle(rotated)
    assert isinstance(angle, float)

    deskewed, final_angle = preprocessor.deskew(rotated)
    assert isinstance(deskewed, Image.Image)


def test_detect_roi(sample_medicine_image):
    img = preprocessor.load_image(sample_medicine_image)
    roi = preprocessor.detect_roi(img)
    assert "x" in roi and "y" in roi and "w" in roi and "h" in roi
    assert roi["w"] > 0
    assert roi["h"] > 0
    assert roi["confidence"] > 0.5


def test_full_preprocessing_pipeline(sample_medicine_image):
    res = preprocessor.process(sample_medicine_image)
    assert "roi" in res
    assert "skew_angle" in res
    assert "processed_base64" in res
    assert res["processed_base64"].startswith("data:image/jpeg;base64,")

