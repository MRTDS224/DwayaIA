import pytest
from challenge1.app.core.normalizer import (
    normalize_query, transliterate_arabizi, clean_arabic_text, detect_script
)

def test_transliterate_arabizi():
    assert "aafak" in transliterate_arabizi("3afak")
    assert "h" in transliterate_arabizi("7abba")
    assert "q" in transliterate_arabizi("9elb")

def test_normalize_french_accents():
    raw = "Médicament à base d'Amoxicilline générique !"
    norm = normalize_query(raw)
    assert "medicament a base d amoxicilline generique" in norm
    assert "é" not in norm
    assert "!" not in norm

def test_normalize_arabic_tashkeel():
    raw = "دَوَاءُ البَارَاسِيتَامُول"
    clean = clean_arabic_text(raw)
    assert "َ" not in clean  # pas de fatha
    assert "ُ" not in clean  # pas de damma

def test_detect_script():
    assert detect_script("doliprane 1000") == "latin_or_french"
    assert detect_script("khassni 3afak dwa") == "arabizi"
    assert detect_script("أريد دواء دوليبران") == "arabic"

