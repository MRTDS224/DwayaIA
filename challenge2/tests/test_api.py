import io
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from challenge1.app.main import app

client = TestClient(app)


@pytest.fixture
def dummy_image_file():
    img = Image.new("RGB", (400, 250), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 380, 230], outline=(13, 148, 136), width=3)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return ("test_box.jpg", buf, "image/jpeg")


def test_api_vision_recognize(dummy_image_file):
    files = {"image": dummy_image_file}
    data = {"hint_tokens": "DOLIPRANE, 1000mg"}
    res = client.post("/vision/recognize", files=files, data=data)
    assert res.status_code == 200
    json_data = res.json()

    assert "status" in json_data
    assert "composite_score" in json_data
    assert "roi_box" in json_data
    assert "processed_image_base64" in json_data
    assert "disclaimer" in json_data


def test_api_vision_ocr_extract(dummy_image_file):
    files = {"image": dummy_image_file}
    res = client.post("/vision/ocr-extract", files=files)
    assert res.status_code == 200
    json_data = res.json()

    assert "text_fr" in json_data
    assert "text_ar" in json_data
    assert "conf_ocr" in json_data
    assert "roi_box" in json_data


def test_api_vision_match_catalog():
    payload = {
        "ocr_tokens": ["DOLIPRANE", "1000", "MG"],
        "conf_ocr": 0.90,
    }
    res = client.post("/vision/match-catalog", json=payload)
    assert res.status_code == 200
    json_data = res.json()

    assert json_data["status"] in ["validated", "ambiguous"]
    assert json_data["matched_drug"] is not None
    assert "DOLIPRANE" in json_data["matched_drug"]["nom"].upper()


def test_api_catalog_drug_by_id():
    # Code CIP officiel CNOPS
    cip = "6118001230068"
    res = client.get(f"/catalog/drugs/{cip}")
    assert res.status_code == 200
    json_data = res.json()

    assert json_data["cip"] == cip
    assert "nom" in json_data
    assert "ppv" in json_data
    assert "alternatives_generiques" in json_data

