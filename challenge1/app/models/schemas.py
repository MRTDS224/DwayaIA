"""
Modèles Pydantic pour la validation et documentation OpenAPI/Swagger
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ParseRequest(BaseModel):
    text: str = Field(..., description="Message brut en Darija, Français, Arabizi ou Arabe")
    lang: Optional[str] = Field("auto", description="Langue ou 'auto' pour détection automatique")
    user_lat: Optional[float] = Field(None, description="Latitude GPS du patient")
    user_lng: Optional[float] = Field(None, description="Longitude GPS du patient")

class ExtractedEntities(BaseModel):
    medication: Optional[str] = None
    dosage_val: Optional[str] = None
    dosage_unit: Optional[str] = None
    galenic_form: Optional[str] = None
    location: Optional[str] = None
    raw_entities: Dict[str, Any] = {}

class ParseResponse(BaseModel):
    intent: str
    confidence: float
    detected_script: str
    normalized_text: str
    entities: ExtractedEntities
    needs_clarification: bool = False
    clarification_options: List[str] = []

class DrugSearchRequest(BaseModel):
    query: str
    limit: int = 5
    fuzzy: bool = True

class DrugSummary(BaseModel):
    code: str
    nom: str
    dci: str
    dosage: str
    unite_dosage: str
    forme: str
    presentation: str
    ppv: float
    princeps_generique: str
    taux_remboursement: str
    similarity_score: Optional[float] = None

class DrugDetail(DrugSummary):
    ph: Optional[float] = None
    prix_br: Optional[float] = None

class PharmacySummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    phone: Optional[str] = Field(None, validation_alias="Phone")
    address: Optional[str] = None
    ville: Optional[str] = Field(None, validation_alias="Ville")
    garde: Optional[str] = ""
    lat: float
    lng: float
    distance_km: Optional[float] = None

class AvailabilityRequest(BaseModel):
    cip_code: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    garde_only: bool = False
    limit: int = 10

class ChatRequest(BaseModel):
    message: str
    lat: Optional[float] = None
    lng: Optional[float] = None

class ChatResponse(BaseModel):
    reply_text: str
    intent: str
    confidence: float
    entities: ExtractedEntities
    matched_drug: Optional[DrugSummary] = None
    alternatives: List[DrugSummary] = []
    pharmacies: List[PharmacySummary] = []
    safety_alert: Optional[str] = None
    disclaimer: str = "Assistant informatif logistique et tarifaire. Ne remplace pas la prescription d'un médecin ni le conseil du pharmacien."
