"""Routes FastAPI pour le module Vision & OCR de boîtes de médicaments (Challenge #2).

Endpoints spécifiés :
- POST /vision/recognize
- POST /vision/ocr-extract
- POST /vision/match-catalog
- GET /catalog/drugs/{id}
"""

from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel, Field

from challenge2.vision.service import vision_service
from challenge2.vision.ocr_engine import ocr_engine
from challenge2.vision.matcher import product_matcher
from challenge2.vision.preprocessor import preprocessor
from challenge1.app.services.catalog_service import catalog_service

router = APIRouter(prefix="", tags=["Vision & OCR"])


class MatchCatalogRequest(BaseModel):
    ocr_tokens: List[str] = Field(..., description="Liste de tokens extraits par l'OCR")
    conf_ocr: float = Field(0.85, description="Confiance moyenne estimée de l'OCR")


@router.post("/vision/recognize")
async def recognize_medication_box(
    image: UploadFile = File(..., description="Fichier image de la boîte de médicament (JPEG/PNG)"),
    hint_tokens: Optional[str] = Form(None, description="Tokens optionnels séparés par des virgules pour guider le matching"),
):
    """Pipeline complet : Prétraitement -> OCR bilingue -> Matching CNOPS -> Alternatives."""
    try:
        content = await image.read()
        if not content:
            raise HTTPException(status_code=400, detail="Fichier image vide.")

        hints = [t.strip() for t in hint_tokens.split(",")] if hint_tokens else None
        result = vision_service.process_medication_image(content, hint_tokens=hints)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de traitement vision : {str(e)}")


@router.post("/vision/ocr-extract")
async def extract_ocr_text(
    image: UploadFile = File(..., description="Fichier image de la boîte"),
):
    """Extraction brute du texte bilingue (Français & Arabe) avec boîtes et confiance."""
    try:
        content = await image.read()
        if not content:
            raise HTTPException(status_code=400, detail="Fichier image vide.")

        prep = preprocessor.process(content)
        ocr_res = ocr_engine.extract_text(prep["processed_image"])

        return {
            "text_fr": ocr_res["text_fr"],
            "text_ar": ocr_res["text_ar"],
            "tokens": ocr_res["all_tokens"],
            "detected_dosages": ocr_res["detected_dosages"],
            "conf_ocr": ocr_res["conf_ocr"],
            "text_boxes": ocr_res["text_boxes"],
            "roi_box": prep["roi"],
            "skew_angle": prep["skew_angle"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'extraction OCR : {str(e)}")


@router.post("/vision/match-catalog")
async def match_catalog_tokens(payload: MatchCatalogRequest):
    """Appariement lexical et multi-attributs contre les 5 918 médicaments CNOPS."""
    try:
        result = product_matcher.match_tokens(
            tokens=payload.ocr_tokens,
            conf_ocr=payload.conf_ocr,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'appariement catalogue : {str(e)}")


@router.get("/catalog/drugs/{drug_id}")
async def get_drug_details(drug_id: str):
    """Fiche produit détaillée CNOPS/DMP par code CIP."""
    drug = catalog_service.get_by_code(drug_id)
    if not drug:
        # Tenter par recherche souple sur le code CIP
        for d in catalog_service.drugs:
            if str(d.get("code", "")).strip().lower() == str(drug_id).strip().lower():
                drug = d
                break

    if not drug:
        raise HTTPException(
            status_code=404,
            detail=f"Médicament avec le code CIP '{drug_id}' introuvable dans le référentiel CNOPS.",
        )

    # Récupérer les alternatives génériques équivalentes
    alternatives = []
    cip = drug.get("code", "")
    alts = catalog_service.get_alternatives(cip)
    for a in alts[:5]:
        alternatives.append({
            "cip": a.get("code", ""),
            "nom": a.get("nom", ""),
            "dosage": a.get("dosage", ""),
            "forme": a.get("forme", ""),
            "ppv": a.get("ppv", 0.0),
            "savings_mad": round(drug.get("ppv", 0.0) - a.get("ppv", 0.0), 2),
        })

    return {
        "code": drug.get("code", ""),
        "cip": drug.get("code", ""),
        "nom": drug.get("nom", ""),
        "dci": drug.get("dci", ""),
        "dosage": drug.get("dosage", ""),
        "forme": drug.get("forme", ""),
        "presentation": drug.get("presentation", ""),
        "ppv": drug.get("ppv", 0.0),
        "ph": drug.get("ph", 0.0),
        "prix_br": drug.get("prix_br", 0.0),
        "is_generique": drug.get("princeps_generique") == "Générique",
        "alternatives_generiques": alternatives,
        "remboursement_amo": "Pris en charge selon le taux réglementaire CNOPS/CNSS",
    }
