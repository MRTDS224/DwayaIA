import pytest
from challenge2.vision.matcher import product_matcher


def test_normalize_ocr_characters():
    raw = "D0L1PRANE 1000MG!"
    norm = product_matcher.normalize_text_for_matching(raw)
    assert "DOLIPRANE" in norm


def test_extract_dosage():
    assert product_matcher.extract_dosage("Doliprane 1000mg") == "1000 MG"
    assert product_matcher.extract_dosage("Augmentin 1g comprimé") == "1 G"
    assert product_matcher.extract_dosage("Aspegic 500 mg sachet") == "500 MG"
    assert product_matcher.extract_dosage("Aspirine") is None


def test_matching_cnops_exact_and_fuzzy():
    # Test avec légères erreurs OCR
    tokens = ["D0L1PRANE", "1000", "MG"]
    res = product_matcher.match_tokens(tokens, conf_ocr=0.90)

    assert res["status"] in ["validated", "ambiguous"]
    assert res["matched_drug"] is not None
    assert "DOLIPRANE" in res["matched_drug"]["nom"].upper()
    assert res["composite_score"] >= 0.80
    assert "disclaimer" in res


def test_dosage_disambiguation():
    # Doliprane 500mg doit ressortir en premier plutôt que 1000mg
    res_500 = product_matcher.match_tokens(["DOLIPRANE", "500", "MG"], conf_ocr=0.90)
    assert res_500["matched_drug"] is not None
    assert "500" in res_500["matched_drug"]["nom"] or "500" in str(res_500["matched_drug"]["dosage"])

    # Doliprane 1000mg / 1g (dans CNOPS, le dosage est stocké comme '1' avec unité 'G' ou '1000 MG')
    res_1000 = product_matcher.match_tokens(["DOLIPRANE", "1000", "MG"], conf_ocr=0.90)
    assert res_1000["matched_drug"] is not None
    dosage_str = str(res_1000["matched_drug"]["dosage"])
    assert dosage_str in ["1", "1000"] or "1000" in res_1000["matched_drug"]["nom"] or "1G" in res_1000["matched_drug"]["nom"]


def test_decision_thresholds_rejection():
    # Mots charabia ne correspondant à rien
    tokens = ["XYZ9876QWERTY", "UNKNOWNMOLECULE"]
    res = product_matcher.match_tokens(tokens, conf_ocr=0.50)
    assert res["status"] == "rejected"
    assert res["matched_drug"] is None
    assert "message" in res
