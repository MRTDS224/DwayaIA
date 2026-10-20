"""
Module de normalisation et de translittération pour requêtes multilingues :
Arabe, Darija (écriture arabe), Arabizi (chiffres 3, 7, 9) et Français.
"""
import re
import unicodedata

# Mappage phonétique des chiffres de l'Arabizi vers des approximations latines / arabes
ARABIZI_MAP = {
    '3': 'aa',   # Ain (ع)
    '7': 'h',    # Haa (ح)
    '9': 'q',    # Qaf (ق)
    '5': 'kh',   # Khaa (خ)
    '2': 'a',    # Hamza (ء)
    '8': 'gh',   # Ghayn (غ)
}

# Diacritiques arabes (Tashkeel)
ARABIC_DIACRITICS = re.compile(r'[\u0617-\u061A\u064B-\u0652]')

def remove_accents(text: str) -> str:
    """Supprime les accents de la langue française."""
    nfkd_form = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def clean_arabic_text(text: str) -> str:
    """Normalise l'écriture arabe (suppression tashkeel, unification alef et yaa)."""
    text = re.sub(ARABIC_DIACRITICS, '', text)
    # Unifier les formes de Alif
    text = re.sub(r'[إأآا]', 'ا', text)
    # Unifier Taa Marbuta / Haa
    text = re.sub(r'ة', 'ه', text)
    # Unifier Yaa / Alif Maqsura
    text = re.sub(r'ى', 'ي', text)
    return text

def transliterate_arabizi(text: str) -> str:
    """
    Remplace les chiffres arabizi isolés ou inclus dans les mots.
    Exemple: '3afak' -> 'aafak' ou 'khassni'
    """
    res = []
    for char in text:
        if char in ARABIZI_MAP:
            res.append(ARABIZI_MAP[char])
        else:
            res.append(char)
    return "".join(res)

def normalize_query(text: str) -> str:
    """
    Pipeline global de normalisation textuelle pour le NLU :
    1. Minuscules
    2. Suppression des accents français
    3. Normalisation arabe
    4. Nettoyage de la ponctuation superflue tout en gardant les unités (mg, g, ml)
    """
    if not text:
        return ""
    
    text = text.strip().lower()
    text = remove_accents(text)
    text = clean_arabic_text(text)
    
    # Remplacer les tirets et underscores par des espaces
    text = re.sub(r'[-_]', ' ', text)
    # Supprimer les ponctuations interrogatives ou d'exclamation
    text = re.sub(r'[?!.,;:\'\"()\[\]{}]', ' ', text)
    # Normaliser les espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def detect_script(text: str) -> str:
    """Détecte l'alphabet dominant du texte (latin/arabizi ou arabe)."""
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    latin_chars = len(re.findall(r'[a-zA-Z]', text))
    
    if arabic_chars > latin_chars:
        return "arabic"
    elif any(d in text for d in ['3', '7', '9', '5']) and latin_chars > 0:
        return "arabizi"
    return "latin_or_french"
