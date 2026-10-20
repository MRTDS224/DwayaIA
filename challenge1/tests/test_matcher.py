import pytest
from challenge1.app.services.catalog_service import catalog_service

def test_catalog_loaded():
    assert len(catalog_service.drugs) > 5000
    assert len(catalog_service.drug_names_lower) > 5000

def test_fuzzy_search_typos():
    # Test avec faute de frappe "doli"
    res1 = catalog_service.search("doli 1000", limit=3)
    assert len(res1) > 0
    assert "DOLIPRANE" in res1[0]["nom"]

    # Test avec faute "augmantin"
    res2 = catalog_service.search("augmantin", limit=3)
    assert len(res2) > 0
    assert "AUGMENTIN" in res2[0]["nom"]

def test_alternatives_dci():
    # Récupérer un médicament connu comme princeps
    clamoxyl_list = catalog_service.search("CLAMOXYL 1 G", limit=1)
    assert len(clamoxyl_list) > 0
    target = clamoxyl_list[0]
    
    # Trouver ses génériques (même DCI AMOXICILLINE)
    alts = catalog_service.get_alternatives(target["code"])
    assert len(alts) > 0
    assert any("AMOXIL" in a["nom"] or "AMOXICILLINE" in a["dci"] for a in alts)
