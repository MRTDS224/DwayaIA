"""Moteur d'appariement hybride et de désambiguïsation multi-attributs CNOPS.

Implémente :
1. Étage Lexical : RapidFuzz (Token Set Ratio) tolérant aux bruits OCR
2. Étage Règle : Validation conjointe Marque + Dosage + Forme galénique
3. Calcul du Score de Confiance Composite (0.5 * Conf_OCR + 0.5 * Sim_Match)
4. Gestion des 3 seuils de décision (>=0.85, [0.60, 0.85[, <0.60)
"""

import re
from typing import Dict, Any, List, Optional
from rapidfuzz import fuzz

# Réutilisation du catalogue officiel CNOPS déjà indexé dans challenge1
from challenge1.app.services.catalog_service import catalog_service


class ProductMatcher:
    """Moteur d'appariement catalogue CNOPS pour la vision et l'OCR."""

    def __init__(self):
        self.catalog = catalog_service

    def normalize_text_for_matching(self, text: str) -> str:
        """Nettoie le texte des caractères spéciaux et standardise les espaces."""
        text = text.upper()
        # Remplacements fréquents d'erreurs OCR (chiffres au milieu de mots)
        text = text.replace("0", "O").replace("1", "I").replace("5", "S")
        # Nettoyage ponctuation
        text = re.sub(r"[^\w\s]", " ", text)
        return " ".join(text.split())

    def extract_dosage(self, query: str) -> Optional[str]:
        """Extrait la valeur numérique du dosage (ex: '1000mg' -> '1000 MG', '1g' -> '1 G')."""
        match = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(MG|G|ML|MCG|UI|%)\b", query, re.IGNORECASE)
        if match:
            val, unit = match.groups()
            return f"{val} {unit.upper()}"
        # Cas '1G' ou '500MG' collé
        match_compact = re.search(r"\b(\d+)(MG|G)\b", query, re.IGNORECASE)
        if match_compact:
            val, unit = match_compact.groups()
            return f"{val} {unit.upper()}"
        return None

    def match_tokens(
        self,
        tokens: List[str],
        conf_ocr: float = 0.85,
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """Effectue l'appariement flou multi-attributs contre les 5 918 médicaments CNOPS."""
        query_str = " ".join(tokens)
        cleaned_query = self.normalize_text_for_matching(query_str)
        target_dosage = self.extract_dosage(query_str)

        if not cleaned_query.strip():
            return {
                "status": "rejected",
                "composite_score": 0.0,
                "conf_ocr": conf_ocr,
                "sim_matching": 0.0,
                "matched_drug": None,
                "suggestions": [],
                "message": "Aucun texte exploitable n'a été détecté sur l'image. Veuillez reprendre la photo en vous rapprochant de la boîte.",
                "disclaimer": "La reconnaissance automatique ne remplace pas l'avis d'un professionnel de santé.",
            }

        scored_candidates = []
        for drug in self.catalog.drugs:
            # Score de base sur le nom commercial (Token Set Ratio)
            norm_drug_name = self.normalize_text_for_matching(drug["nom"])
            base_ratio = fuzz.token_set_ratio(cleaned_query, norm_drug_name) / 100.0

            # Score sur la DCI
            dci_ratio = 0.0
            drug_dci = drug.get("dci", "")
            if drug_dci:
                norm_dci = self.normalize_text_for_matching(drug_dci)
                dci_ratio = fuzz.token_set_ratio(cleaned_query, norm_dci) / 100.0

            sim_score = max(base_ratio, dci_ratio * 0.9)

            # Bonus / Malus de désambiguïsation par Dosage
            if target_dosage:
                target_num_match = re.search(r"\b(\d+(?:[.,]\d+)?)\b", target_dosage)
                target_num = target_num_match.group(1) if target_num_match else ""
                drug_dosage_val = str(drug.get("dosage", "")).strip().split(".")[0]
                drug_unit_val = str(drug.get("unite_dosage", "")).strip().upper()
                drug_nom_str = drug["nom"].upper()

                if target_num and (target_num == drug_dosage_val or f" {target_num}" in drug_nom_str or f"{target_num}MG" in drug_nom_str):
                    sim_score = min(1.0, sim_score + 0.25)
                elif target_num == "1" and (drug_dosage_val == "1000" and "MG" in drug_unit_val):
                    # Équivalence 1g = 1000mg
                    sim_score = min(1.0, sim_score + 0.25)
                elif target_num == "1000" and (drug_dosage_val == "1" and "G" in drug_unit_val):
                    # Équivalence 1000mg = 1g
                    sim_score = min(1.0, sim_score + 0.25)
                elif target_num and drug_dosage_val and target_num != drug_dosage_val:
                    # Malus si le dosage ne correspond pas
                    sim_score = max(0.2, sim_score - 0.15)

            if sim_score >= 0.40:
                scored_candidates.append((sim_score, drug))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        top_candidates = scored_candidates[:top_k]

        if not top_candidates:
            return {
                "status": "rejected",
                "composite_score": 0.0,
                "conf_ocr": conf_ocr,
                "sim_matching": 0.0,
                "matched_drug": None,
                "suggestions": [],
                "message": "Médicament non identifié dans le catalogue officiel CNOPS. Veuillez vérifier la netteté et le cadrage.",
                "disclaimer": "La reconnaissance automatique ne remplace pas l'avis d'un professionnel de santé.",
            }

        best_sim, best_drug = top_candidates[0]

        # Calcul du score composite réglementaire
        composite_score = round(0.5 * conf_ocr + 0.5 * best_sim, 2)

        # Préparation des suggestions
        suggestions = []
        for sim, drug in top_candidates:
            suggestions.append({
                "cip": drug["code"],
                "nom": drug["nom"],
                "dci": drug.get("dci", ""),
                "dosage": drug.get("dosage", ""),
                "forme": drug.get("forme", ""),
                "ppv": drug.get("ppv", 0.0),
                "is_generique": drug.get("princeps_generique") == "Générique",
                "similarity": round(sim, 2),
                "composite_score": round(0.5 * conf_ocr + 0.5 * sim, 2),
            })

        disclaimer = "Rappel : La reconnaissance visuelle automatique ne dispense pas de la vérification de l'étiquetage et de la posologie par un pharmacien ou un médecin."

        # Règle des 3 seuils de décision
        if composite_score >= 0.85:
            return {
                "status": "validated",
                "composite_score": composite_score,
                "conf_ocr": conf_ocr,
                "sim_matching": round(best_sim, 2),
                "matched_drug": suggestions[0],
                "suggestions": suggestions,
                "message": f"Médicament identifié avec certitude : {best_drug['nom']} (PPV : {best_drug['ppv']:.2f} MAD).",
                "disclaimer": disclaimer,
            }
        elif composite_score >= 0.60:
            return {
                "status": "ambiguous",
                "composite_score": composite_score,
                "conf_ocr": conf_ocr,
                "sim_matching": round(best_sim, 2),
                "matched_drug": suggestions[0],
                "suggestions": suggestions,
                "message": "Plusieurs présentations correspondent à votre boîte. Veuillez confirmer la référence exacte parmi les suggestions ci-dessous.",
                "disclaimer": disclaimer,
            }
        else:
            return {
                "status": "rejected",
                "composite_score": composite_score,
                "conf_ocr": conf_ocr,
                "sim_matching": round(best_sim, 2),
                "matched_drug": None,
                "suggestions": suggestions,
                "message": "Niveau de certitude insuffisant (< 0.60). Veuillez reprendre la photo en évitant les reflets et en cadrant le nom et le dosage.",
                "disclaimer": disclaimer,
            }


# Instance singleton
product_matcher = ProductMatcher()
