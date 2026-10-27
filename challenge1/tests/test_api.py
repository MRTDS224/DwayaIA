import pytest
from fastapi.testclient import TestClient
from challenge1.app.main import app

client = TestClient(app)

def test_root_ui_serves_html():
    res = client.get("/")
    assert res.status_code == 200
    assert "Dwaya AI" in res.text

def test_api_nlu_parse():
    res = client.post("/api/nlu/parse", json={"text": "khassni doliprane 1g f agadir"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "check_availability"
    assert data["entities"]["location"] == "Agadir"

def test_api_catalog_search():
    res = client.post("/api/catalog/search", json={"query": "dolipran 1000", "limit": 3})
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    assert "DOLIPRANE" in data[0]["nom"]

def test_api_catalog_drug_detail():
    # Code d'un médicament connu
    cip = "6118001230068"
    res = client.get(f"/api/catalog/drugs/{cip}")
    assert res.status_code == 200
    data = res.json()
    assert data["code"] == cip
    assert "ppv" in data

def test_api_pharmacies():
    res = client.post("/api/pharmacies/availability", json={"city": "Agadir", "limit": 5})
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    assert data[0]["ville"] == "Agadir"

def test_api_chat_orchestrator():
    res = client.post("/api/chat", json={"message": "prix dial augmentin 1g svp"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "ask_price_reimbursement"
    assert data["matched_drug"] is not None
    assert "AUGMENTIN" in data["matched_drug"]["nom"]

def test_api_pharmacies_with_quick_actions():
    res = client.post("/api/pharmacies/availability", json={"city": "Casablanca", "limit": 3})
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    p = data[0]
    assert "maps_url" in p
    assert "phone_url" in p
    assert "whatsapp_url" in p

def test_api_chat_multimodal_multipart():
    from pathlib import Path
    sample_img = Path("challenge2/data/samples/doliprane_1000mg.webp")
    if sample_img.exists():
        with open(sample_img, "rb") as f:
            files = {"image": ("doliprane.webp", f.read(), "image/webp")}
            data = {"message": "Chhal dayr had dwa f pharmacie ?"}
            res = client.post("/api/chat/multimodal", data=data, files=files)
            assert res.status_code == 200
            res_data = res.json()
            assert res_data["matched_drug"] is not None
            assert "DOLIPRANE" in res_data["matched_drug"]["nom"].upper()

