import pytest
from challenge1.app.core.nlu_engine import nlu_engine

def test_intent_classification():
    # 1. Disponibilité
    res1 = nlu_engine.parse("khassni doliprane 1g 3afak fin nqder nlqah daba casablanca")
    assert res1.intent == "check_availability"
    assert res1.entities.location == "Casablanca"
    assert res1.entities.dosage_val == "1"

    # 2. Prix et Remboursement
    res2 = nlu_engine.parse("chhal taman dial augmentin 1g wa wach remboursable cnops")
    assert res2.intent == "ask_price_reimbursement"

    # 3. Alternatives / Génériques
    res3 = nlu_engine.parse("malqitch clamoxyl bghit generique f blastou")
    assert res3.intent == "find_alternatives"

    # 4. Posologie
    res4 = nlu_engine.parse("chhal mn habba f nhar dial spasfon")
    assert res4.intent == "ask_posology_usage"

    # 5. Effets indésirables / Sécurité
    res5 = nlu_engine.parse("wach doliprane fih khatar l la femme enceinte")
    assert res5.intent == "ask_side_effects_safety"

def test_emergency_guardrail():
    # Alerte d'urgence
    alert = nlu_engine.check_emergency("3andi wja3 f sadri bzaf w tkhneqt")
    assert alert is not None
    assert "SAMU" in alert
