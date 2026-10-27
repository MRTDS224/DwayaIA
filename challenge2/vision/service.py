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

        # 2. Extraction OCR Bilingue
        ocr_res = self.ocr_engine.extract_text(processed_img, hint_tokens=hint_tokens)

        # 3. Matching CNOPS & Scoring Composite
        match_res = self.matcher.match_tokens(
            tokens=ocr_res["all_tokens"],
            conf_ocr=ocr_res["conf_ocr"],
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
                "fr": ocr_res["text_fr"],
                "ar": ocr_res["text_ar"],
                "tokens": ocr_res["all_tokens"],
                "dosages": ocr_res["detected_dosages"],
            },
            "processed_image_base64": prep_res["processed_base64"],
        }


# Instance singleton
vision_service = VisionService()
