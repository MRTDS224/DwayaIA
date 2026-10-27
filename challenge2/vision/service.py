"""Service d'orchestration pour le pipeline Vision & OCR.

Coordonne :
1. Prétraitement d'image (RoI, CLAHE, Deskew)
2. Extraction OCR Bilingue (Arabe / Français)
3. Appariement CNOPS avec désambiguïsation multi-attributs
4. Enrichissement pharmaco-économique (alternatives génériques CNOPS)
"""

from typing import Dict, Any, List, Optional
from challenge2.vision.preprocessor import preprocessor
from challenge2.vision.ocr_engine import ocr_engine
from challenge2.vision.matcher import product_matcher
from challenge1.app.services.catalog_service import catalog_service


class VisionService:
    """Service d'orchestration end-to-end pour la reconnaissance de boîtes."""

    def __init__(self):
        self.preprocessor = preprocessor
        self.ocr_engine = ocr_engine
        self.matcher = product_matcher
        self.catalog = catalog_service

    def process_medication_image(
        self,
        image_bytes: bytes,
        hint_tokens: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Exécute l'intégralité du pipeline Vision & OCR à partir d'une image brute."""
        # 1. Prétraitement géométrique et photométrique
        prep_res = self.preprocessor.process(image_bytes)
        processed_img = prep_res["processed_image"]

        # 2. Extraction OCR Bilingue (Double passe : Image brute couleur + Image rehaussée CLAHE)
        original_img = self.preprocessor.load_image(image_bytes)
        ocr_res_orig = self.ocr_engine.extract_text(original_img, hint_tokens=hint_tokens)
        ocr_res_prep = self.ocr_engine.extract_text(processed_img, hint_tokens=hint_tokens)

        # Union des tokens pour maximiser le rappel (marques colorées + petits caractères)
        combined_tokens = list(dict.fromkeys(ocr_res_orig["all_tokens"] + ocr_res_prep["all_tokens"]))
        all_boxes = ocr_res_orig["text_boxes"] or ocr_res_prep["text_boxes"]
        best_conf = max(ocr_res_orig["conf_ocr"], ocr_res_prep["conf_ocr"])

        # 3. Matching CNOPS & Scoring Composite
        match_res = self.matcher.match_tokens(
            tokens=combined_tokens,
            conf_ocr=best_conf,
        )

        # 4. Enrichissement avec alternatives génériques si un médicament est identifié
        generics_list = []
        if match_res["matched_drug"] and match_res["matched_drug"].get("cip"):
            matched_cip = match_res["matched_drug"]["cip"]
            alts = self.catalog.get_alternatives(matched_cip)
            for a in alts[:3]:
                generics_list.append({
                    "cip": a["code"],
                    "nom": a["nom"],
                    "dosage": a.get("dosage", ""),
                    "forme": a.get("forme", ""),
                    "ppv": a.get("ppv", 0.0),
                    "savings_mad": round(match_res["matched_drug"]["ppv"] - a.get("ppv", 0.0), 2),
                })

        return {
            "status": match_res["status"],
            "composite_score": match_res["composite_score"],
            "conf_ocr": match_res["conf_ocr"],
            "sim_matching": match_res["sim_matching"],
            "matched_drug": match_res["matched_drug"],
            "suggestions": match_res["suggestions"],
            "generics": generics_list,
            "message": match_res["message"],
            "disclaimer": match_res["disclaimer"],
            "roi_box": prep_res["roi"],
            "skew_angle": prep_res["skew_angle"],
            "extracted_text": {
                "fr": f"{ocr_res_orig['text_fr']} {ocr_res_prep['text_fr']}".strip(),
                "ar": f"{ocr_res_orig['text_ar']} {ocr_res_prep['text_ar']}".strip(),
                "tokens": combined_tokens,
                "dosages": list(set(ocr_res_orig["detected_dosages"] + ocr_res_prep["detected_dosages"])),
            },
            "processed_image_base64": prep_res["processed_base64"],
        }


# Instance singleton
vision_service = VisionService()
