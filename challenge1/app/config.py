"""
Configuration globale de l'application Challenge 1
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

DATA_DIR = BASE_DIR / "data"
MEDICAMENTS_FILE = DATA_DIR / "ref-des-medicaments-cnops-2014.xlsx"
PHARMACIES_FILE = DATA_DIR / "pharmacies_maroc.json"

# Coordonnées par défaut (Casablanca) si aucune localisation n'est spécifiée
DEFAULT_LAT = 33.5731
DEFAULT_LNG = -7.5898

# Seuils de confiance NLU
CONFIDENCE_HIGH_THRESHOLD = 0.85
CONFIDENCE_MEDIUM_THRESHOLD = 0.60

