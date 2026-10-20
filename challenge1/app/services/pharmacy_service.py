"""
Service de recherche d'officines et de pharmacies de garde au Maroc
Calcul de distances géodésiques par la formule de Haversine.
"""
import json
import math
from typing import List, Optional, Dict
from challenge1.app.config import PHARMACIES_FILE, DEFAULT_LAT, DEFAULT_LNG
from challenge1.app.core.normalizer import normalize_query

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcule la distance en kilomètres entre deux coordonnées géographiques (formule de Haversine)."""
    R = 6371.0  # Rayon de la Terre en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

class PharmacyService:
    def __init__(self):
        self.pharmacies: List[Dict] = []
        self.pharmacies_by_city: Dict[str, List[Dict]] = {}
        self._load_data()

    def _load_data(self):
        """Charge les 800 officines collectées via Saydalia API."""
        if not PHARMACIES_FILE.exists():
            print(f"[!] Fichier des pharmacies non trouvé: {PHARMACIES_FILE}")
            return

        with open(PHARMACIES_FILE, "r", encoding="utf-8") as f:
            self.pharmacies = json.load(f)

        for p in self.pharmacies:
            city = p.get("Ville", "").strip()
            norm_city = normalize_query(city)
            if norm_city:
                if norm_city not in self.pharmacies_by_city:
                    self.pharmacies_by_city[norm_city] = []
                self.pharmacies_by_city[norm_city].append(p)

        print(f"[✓] Référentiel Pharmacies chargé : {len(self.pharmacies)} officines en mémoire.")

    def search_nearby(
        self, 
        lat: Optional[float] = None, 
        lng: Optional[float] = None, 
        city: Optional[str] = None,
        garde_only: bool = False,
        limit: int = 10
    ) -> List[Dict]:
        """
        Recherche les pharmacies les plus proches avec support de filtrage par garde et ville.
        """
        results = []

        # Filtrage par ville si spécifié
        pool = self.pharmacies
        if city:
            norm_city = normalize_query(city)
            # Trouver la ville la plus proche dans l'index
            matching_cities = [c for c in self.pharmacies_by_city.keys() if norm_city in c or c in norm_city]
            if matching_cities:
                pool = []
                for c in matching_cities:
                    pool.extend(self.pharmacies_by_city[c])

        # Filtrage par garde si demandé
        if garde_only:
            pool = [p for p in pool if p.get("garde")]

        # Si coordonnées disponibles, calculer les distances et trier
        origin_lat = lat if lat is not None else (pool[0]["lat"] if pool else DEFAULT_LAT)
        origin_lng = lng if lng is not None else (pool[0]["lng"] if pool else DEFAULT_LNG)

        for p in pool:
            p_copy = p.copy()
            plat = p.get("lat")
            plng = p.get("lng")
            if plat and plng:
                dist = haversine_distance(origin_lat, origin_lng, float(plat), float(plng))
                p_copy["distance_km"] = dist
            else:
                p_copy["distance_km"] = 999.0
            results.append(p_copy)

        # Trier par présence de garde d'abord (priorité) puis par distance
        results.sort(key=lambda x: (0 if x.get("garde") else 1, x.get("distance_km", 999.0)))
        return results[:limit]

# Instance singleton partagée
pharmacy_service = PharmacyService()

