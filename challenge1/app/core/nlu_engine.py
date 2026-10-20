"""
Moteur NLU (Natural Language Understanding) hybride :
1. Classification des 5 intentions métier
2. Extraction conjointe des entités (Marque, DCI, Dosage, Forme, Ville)
3. Gestion des gardes-fous médicaux d'urgence
"""
import re
from typing import Dict, Any, List, Optional
from challenge1.app.core.normalizer import normalize_query, transliterate_arabizi, detect_script
from challenge1.app.models.schemas import ExtractedEntities, ParseResponse

# Lexique des Villes Marocaines
MOROCCO_CITIES = [
    "casablanca", "casa", "rabat", "sale", "agadir", "marrakech", "kech", "tanger", 
    "fes", "fez", "meknes", "oujda", "tetouan", "kenitra", "safi", "el jadida", 
    "nador", "beni mellal", "khouribga", "laayoune", "dakhla", "taza", "mohammedia"
]

# Formes galéniques usuelles (Français et Darija)
GALENIC_FORMS = {
    "comprime": "Comprimé",
    "comprimes": "Comprimé",
    "habba": "Comprimé",
    "habbat": "Comprimé",
    "fanid": "Comprimé",
    "fanida": "Comprimé",
    "sirop": "Sirop",
    "sirou": "Sirop",
    "gelule": "Gélule",
    "gelules": "Gélule",
    "sachet": "Sachet",
    "sachets": "Sachet",
    "khnichat": "Sachet",
    "suppositoire": "Suppositoire",
    "suppo": "Suppositoire",
    "crachat": "Suppositoire",
    "pommade": "Pommade",
    "marham": "Pommade",
    "gouttes": "Gouttes",
    "injection": "Injectable",
    "ibra": "Injectable"
}

# Détecteurs de Mots-clés pour les Intentions
INTENT_PATTERNS = {
    "ask_price_reimbursement": [
        "prix", "cout", "chhal", "taman", "thaman", "bchhal", "rembourse", "remboursement", 
        "cnops", "amo", "tarification", "tarife", "b kem", "kam"
    ],
    "find_alternatives": [
        "alternative", "remplacant", "remplacement", "generique", "blastou", "f blastou", 
        "chi haja khrina", "chi dwa akhor", "chbih", "equivalent", "substitut"
    ],
    "ask_posology_usage": [
        "posologie", "kifach nakhd", "chhal mn mra", "avant repas", "apres repas", 
        "chhal mn habba", "combien par jour", "mode d emploi", "comment prendre", 
        "f nhar", "kifach nsta3mlou", "isti3mal"
    ],
    "ask_side_effects_safety": [
        "effet secondaire", "effets secondaires", "khatir", "a3rad", "khatar", "danger", 
        "enceinte", "grossesse", "contraindication", "harm", "moudir", "khayf"
    ],
    "check_availability": [
        "dispo", "disponible", "disponibilite", "fin nlqah", "fin kayn", "kayn", "wacha kayn", 
        "ou trouver", "cherche", "bghit", "khassni", "pharmacie", "saydaliya", "saydalia", 
        "garde", "de garde", "nuit", "layliya", "daba"
    ]
}

# Mots-clés d'Urgence Médicale
EMERGENCY_KEYWORDS = [
    "douleur poitrine", "wja3 f sadri", "crise cardiaque", "perte de connaissance", 
    "ghaybouba", "hemorragie", "sang", "dm bzaf", "etouffement", "tkhneqt", "urgence"
]

class NLUEngine:
    def __init__(self):
        pass

    def check_emergency(self, text: str) -> Optional[str]:
        """Détecte les expressions de danger ou d'urgence médicale vitale."""
        norm = normalize_query(text)
        arabizi = transliterate_arabizi(norm)
        for kw in EMERGENCY_KEYWORDS:
            if kw in norm or kw in arabizi:
                return (
                    "⚠️ ALERTE D'URGENCE MÉDICALE DÉTECTÉE : Vos symptômes nécessitent une prise en charge médicale "
                    "immédiate. Veuillez contacter sans attendre le SAMU (150) ou la Protection Civile (141) ou vous "
                    "rendre au service des urgences le plus proche."
                )
        return None

    def extract_dosage(self, text: str) -> (Optional[str], Optional[str]):
        """Extrait la valeur et l'unité de dosage (ex: 1000 mg, 1g, 500mg, 125ml)."""
        pattern = r'(\d+(?:[\.,]\d+)?)\s*(mg|g|ml|mcg|ui|%)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).replace(',', '.'), match.group(2).upper()
        
        # Chiffres isolés après le mot
        pattern_num = r'\b(\d{2,4})\b'
        num_match = re.search(pattern_num, text)
        if num_match:
            val = num_match.group(1)
            # Hypothèse usuelle en mg si > 100
            unit = "MG" if int(val) >= 50 else "G"
            return val, unit
        
        return None, None

    def extract_entities(self, text: str) -> ExtractedEntities:
        """Extrait les entités géographiques, galéniques, posologiques et les noms candidats."""
        norm = normalize_query(text)
        words = norm.split()
        
        # 1. Ville
        detected_city = None
        for w in words:
            if w in MOROCCO_CITIES:
                detected_city = w.capitalize()
                break
        
        # 2. Forme Galénique
        detected_form = None
        for w in words:
            if w in GALENIC_FORMS:
                detected_form = GALENIC_FORMS[w]
                break

        # 3. Dosage
        dosage_val, dosage_unit = self.extract_dosage(norm)

        # 4. Extraction heuristique du nom de médicament (les tokens qui ne sont ni stop-words ni ville/forme)
        stop_words = set([
            "khassni", "bghit", "3afak", "aafak", "fin", "nqder", "nlqah", "daba", "kayn", 
            "wach", "ana", "f", "chhal", "taman", "thaman", "dial", "dyal", "svp", "bonjour", 
            "prix", "du", "de", "la", "le", "les", "des", "pour", "avec", "sans", "est", 
            "rembourse", "par", "cnops", "amo", "pharmacie", "saydalia", "garde", "nuit", "urgent"
        ])
        
        candidate_tokens = []
        for w in words:
            if w not in stop_words and (not detected_city or w != detected_city.lower()) and w not in GALENIC_FORMS:
                # Éviter les unités isolées
                if w not in ["mg", "g", "ml"]:
                    candidate_tokens.append(w)
        
        candidate_med = " ".join(candidate_tokens).strip() if candidate_tokens else None

        return ExtractedEntities(
            medication=candidate_med,
            dosage_val=dosage_val,
            dosage_unit=dosage_unit,
            galenic_form=detected_form,
            location=detected_city,
            raw_entities={"tokens": candidate_tokens}
        )

    def classify_intent(self, text: str) -> (str, float):
        """Classifie l'intention parmi les 5 catégories avec score de confiance."""
        norm = normalize_query(text)
        arabizi = transliterate_arabizi(norm)
        
        scores = {}
        for intent, kws in INTENT_PATTERNS.items():
            matches = 0
            for kw in kws:
                if kw in norm or kw in arabizi:
                    matches += 1
            if matches > 0:
                scores[intent] = matches

        if not scores:
            # Intention par défaut si non déterminée : disponibilité/recherche
            return "check_availability", 0.65

        best_intent = max(scores, key=scores.get)
        # Score normalisé
        confidence = min(0.95, 0.70 + (scores[best_intent] * 0.10))
        return best_intent, round(confidence, 2)

    def parse(self, text: str) -> ParseResponse:
        """Méthode principale d'analyse NLU."""
        norm = normalize_query(text)
        script = detect_script(text)
        intent, confidence = self.classify_intent(text)
        entities = self.extract_entities(text)

        needs_clarification = (confidence < 0.75 or (not entities.medication and intent != "check_availability"))

        clarification_options = []
        if not entities.medication and intent != "check_availability":
            clarification_options = ["Préciser le nom du médicament", "Indiquer votre ville"]

        return ParseResponse(
            intent=intent,
            confidence=confidence,
            detected_script=script,
            normalized_text=norm,
            entities=entities,
            needs_clarification=needs_clarification,
            clarification_options=clarification_options
        )

# Instance singleton partagée
nlu_engine = NLUEngine()
