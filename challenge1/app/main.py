"""
Point d'entrée principal FastAPI pour le Challenge 1 (Assistant Pharmacie)
Expose les 5 endpoints REST modulaires et sert l'interface utilisateur SPA.
"""
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from challenge1.app.models.schemas import (
    ParseRequest, ParseResponse,
    DrugSearchRequest, DrugSummary, DrugDetail,
    AvailabilityRequest, PharmacySummary,
    ChatRequest, ChatResponse
)
from challenge1.app.core.nlu_engine import nlu_engine
from challenge1.app.services.catalog_service import catalog_service
from challenge1.app.services.pharmacy_service import pharmacy_service

app = FastAPI(
    title="Saydalia AI - Pharmacy Assistant API (Challenge #1)",
    description=(
        "Backend intelligent pour requêtes de patients au Maroc. "
        "Supporte le multilinguisme (Darija, Arabizi, Français), l'extraction d'intentions et d'entités, "
        "le matching flou sur la nomenclature officielle CNOPS (5 918 médicaments) et la géolocalisation des officines."
    ),
    version="1.0.0"
)

# Configuration CORS pour permettre les appels depuis n'importe quel client Web ou mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage des fichiers statiques pour l'interface UI
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse, tags=["Interface Utilisateur"])
async def serve_ui():
    """Sert l'interface Web moderne du Chatbot avec inspecteur NLU en temps réel."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>Saydalia Bot API en ligne. Consultez /docs pour la documentation Swagger.</h1>")

# ----------------------------------------------------------------------------------
# Endpoints REST du Pipeline NLP & Catalogue Métier
# ----------------------------------------------------------------------------------

@app.post("/api/nlu/parse", response_model=ParseResponse, tags=["NLP & Parsing"])
async def parse_message(req: ParseRequest):
    """
    Analyse un message utilisateur brut (Darija, Arabizi, Français) :
    1. Normalisation et translittération
    2. Classification de l'intention parmi 5 catégories
    3. Extraction conjointe des entités (médicament, dosage, forme, ville)
    """
    return nlu_engine.parse(req.text)

@app.post("/api/catalog/search", response_model=List[DrugSummary], tags=["Catalogue Médicaments"])
async def search_drugs(req: DrugSearchRequest):
    """
    Recherche floue tolérante aux fautes de frappe (RapidFuzz) dans le référentiel officiel CNOPS.
    """
    results = catalog_service.search(req.query, limit=req.limit)
    return [DrugSummary(**d) for d in results]

@app.get("/api/catalog/drugs/{cip_code}", response_model=DrugDetail, tags=["Catalogue Médicaments"])
async def get_drug_details(cip_code: str):
    """
    Récupère la fiche produit exhaustive par code CIP (DCI, PPV, générique/princeps, remboursement).
    """
    drug = catalog_service.get_by_code(cip_code)
    if not drug:
        raise HTTPException(status_code=404, detail=f"Médicament avec le code CIP {cip_code} introuvable.")
    return DrugDetail(**drug)

@app.get("/api/catalog/drugs/{cip_code}/alternatives", response_model=List[DrugSummary], tags=["Catalogue Médicaments"])
async def get_drug_alternatives(cip_code: str):
    """
    Recherche les génériques et équivalents thérapeutiques partageant la même DCI.
    """
    alts = catalog_service.get_alternatives(cip_code)
    return [DrugSummary(**d) for d in alts]

@app.post("/api/pharmacies/availability", response_model=List[PharmacySummary], tags=["Pharmacies & Géolocalisation"])
async def get_pharmacies(req: AvailabilityRequest):
    """
    Localise les pharmacies les plus proches et les officines de garde à partir de coordonnées GPS ou d'une ville.
    """
    results = pharmacy_service.search_nearby(
        lat=req.lat,
        lng=req.lng,
        city=req.city,
        garde_only=req.garde_only,
        limit=req.limit
    )
    return [PharmacySummary(**p) for p in results]

# ----------------------------------------------------------------------------------
# Endpoint Orchestrateur Tout-en-Un pour l'Expérience Chatbot
# ----------------------------------------------------------------------------------

@app.post("/api/chat", response_model=ChatResponse, tags=["Orchestration Conversationnelle"])
async def chat_interaction(req: ChatRequest):
    """
    Orchestration complète :
    1. Détection des urgences médicales (SAMU 150)
    2. Analyse NLU (Intent + Entités)
    3. Résolution dans le catalogue CNOPS (5 918 médicaments)
    4. Récupération des alternatives génériques si pertinent
    5. Géolocalisation des pharmacies de garde / proches
    6. Formulation d'une réponse claire et structurée
    """
    # 1. Vérification des urgences
    emergency_msg = nlu_engine.check_emergency(req.message)
    if emergency_msg:
        parse_res = nlu_engine.parse(req.message)
        return ChatResponse(
            reply_text=emergency_msg,
            intent="emergency_critical",
            confidence=1.0,
            entities=parse_res.entities,
            safety_alert=emergency_msg
        )

    # 2. Analyse NLU
    nlu_res = nlu_engine.parse(req.message)
    intent = nlu_res.intent
    entities = nlu_res.entities
    
    matched_drug = None
    alternatives = []
    pharmacies = []
    reply_lines = []

    # 3. Résolution du médicament si extrait
    if entities.medication:
        search_query = f"{entities.medication} {entities.dosage_val or ''} {entities.dosage_unit or ''} {entities.galenic_form or ''}".strip()
        candidates = catalog_service.search(search_query, limit=3)
        if candidates:
            matched_drug = DrugSummary(**candidates[0])

    # 4. Traitement selon l'Intention
    if intent == "ask_price_reimbursement":
        if matched_drug:
            reply_lines.append(f"Le prix public de vente (PPV) pour **{matched_drug.nom}** est de **{matched_drug.ppv:.2f} DH**.")
            reply_lines.append(f"Statut : **{matched_drug.princeps_generique}** | Remboursement AMO/CNOPS : **{matched_drug.taux_remboursement}**.")
            if matched_drug.dci:
                reply_lines.append(f"Principe actif (DCI) : *{matched_drug.dci}*.")
        else:
            reply_lines.append("Je n'ai pas pu identifier avec certitude le nom exact du médicament pour vous donner son prix. Pouvez-vous préciser le dosage ou le nom ?")

    elif intent == "find_alternatives":
        if matched_drug:
            alts = catalog_service.get_alternatives(matched_drug.code)
            if alts:
                alternatives = [DrugSummary(**a) for a in alts[:4]]
                reply_lines.append(f"Pour **{matched_drug.nom}** (DCI : *{matched_drug.dci}*), voici les alternatives et génériques équivalents disponibles :")
            else:
                reply_lines.append(f"Aucun générique alternatif trouvé pour {matched_drug.nom} dans la nomenclature officielle.")
        else:
            reply_lines.append("Veuillez préciser le médicament dont vous cherchez le remplaçant ou le générique.")

    elif intent == "ask_posology_usage":
        if matched_drug:
            reply_lines.append(f"Concernant **{matched_drug.nom}** ({matched_drug.forme}) :")
            reply_lines.append("La posologie standard dépend de l'âge, du poids et de la prescription médicale. Respectez scrupuleusement l'ordonnance de votre médecin et l'avis de votre pharmacien.")
        else:
            reply_lines.append("Pour quelle molécule ou quel médicament souhaitez-vous des indications d'usage ?")

    elif intent == "ask_side_effects_safety":
        if matched_drug:
            reply_lines.append(f"Pour **{matched_drug.nom}** (DCI : {matched_drug.dci}) :")
            reply_lines.append("En cas de grossesse, d'allergie connue ou de pathologie chronique, demandez impérativement l'avis de votre médecin ou pharmacien avant toute prise.")
        else:
            reply_lines.append("De quel médicament souhaitez-vous vérifier les contre-indications ?")

    else: # check_availability (par défaut)
        # Recherche des pharmacies proches
        search_city = entities.location
        garde_needed = any(kw in req.message.lower() for kw in ["garde", "nuit", "layliya", "daba"])
        pharm_results = pharmacy_service.search_nearby(
            lat=req.lat,
            lng=req.lng,
            city=search_city,
            garde_only=garde_needed,
            limit=4
        )
        pharmacies = [PharmacySummary(**p) for p in pharm_results]

        if matched_drug:
            reply_lines.append(f"J'ai identifié **{matched_drug.nom}** ({matched_drug.forme}, PPV: {matched_drug.ppv:.2f} DH).")
        
        if pharmacies:
            loc_label = f"à {search_city}" if search_city else "autour de vous"
            garde_label = "de garde " if garde_needed else ""
            reply_lines.append(f"Voici les pharmacies {garde_label}{loc_label} les plus proches :")
        else:
            reply_lines.append("Aucune officine trouvée pour cette localisation. Pouvez-vous indiquer votre ville ?")

    return ChatResponse(
        reply_text=" ".join(reply_lines),
        intent=intent,
        confidence=nlu_res.confidence,
        entities=entities,
        matched_drug=matched_drug,
        alternatives=alternatives,
        pharmacies=pharmacies
    )

