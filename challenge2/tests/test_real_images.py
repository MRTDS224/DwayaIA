"""Tests de validation sur images réelles et échantillons de boîtes marocaines."""

from pathlib import Path
import pytest
from challenge2.vision.service import vision_service

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"


def test_real_user_doliprane_photo():
    """Valide la reconnaissance de la photo réelle de Doliprane 1000 mg fournie par l'utilisateur."""
    img_path = SAMPLES_DIR / "doliprane_1000mg.webp"
    assert img_path.exists(), f"Image non trouvée : {img_path}"

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    res = vision_service.process_medication_image(img_bytes)

    assert res["status"] in ["validated", "ambiguous"]
    assert res["composite_score"] >= 0.85
    assert res["matched_drug"] is not None
    assert "DOLIPRANE" in res["matched_drug"]["nom"].upper()
    assert res["matched_drug"]["dci"] == "PARACETAMOL"
    assert res["matched_drug"]["ppv"] > 0.0
    assert len(res["generics"]) > 0


def test_augmentin_packaging():
    """Valide la détection d'Augmentin 1g."""
    img_path = SAMPLES_DIR / "augmentin_1g.jpg"
    assert img_path.exists()

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    res = vision_service.process_medication_image(img_bytes)

    assert res["status"] in ["validated", "ambiguous"]
    assert res["matched_drug"] is not None
    assert "AUGMENTIN" in res["matched_drug"]["nom"].upper() or "AMOXICILLINE" in res["matched_drug"]["nom"].upper()


def test_kardegic_packaging():
    """Valide la détection de Kardegic 75mg."""
    img_path = SAMPLES_DIR / "kardegic_75mg.jpg"
    assert img_path.exists()

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    res = vision_service.process_medication_image(img_bytes)

    assert res["status"] in ["validated", "ambiguous"]
    assert res["matched_drug"] is not None
    assert "KARDEGIC" in res["matched_drug"]["nom"].upper()
