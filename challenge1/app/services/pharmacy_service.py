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
        limit: int = 10,
        max_radius_km: float = 35.0
    ) -> List[Dict]:
        """
        Recherche les pharmacies strictement les plus proches de la position demandée.
        Priorise d'abord la proximité géographique (< 35km), puis met en avant les gardes.
        """
        pool = self.pharmacies

        # Filtrage par ville si spécifié
        if city:
            norm_city = normalize_query(city)
            matching_cities = [c for c in self.pharmacies_by_city.keys() if norm_city in c or c in norm_city]
            if matching_cities:
                pool = []
                for c in matching_cities:
                    pool.extend(self.pharmacies_by_city[c])

        # Filtrage par garde si demandé
        if garde_only:
            pool = [p for p in pool if p.get("garde")]

        # Détermination du point d'origine
        if lat is not None and lng is not None:
            origin_lat = lat
            origin_lng = lng
        elif city and pool:
            origin_lat = pool[0].get("lat", DEFAULT_LAT)
            origin_lng = pool[0].get("lng", DEFAULT_LNG)
        else:
            origin_lat = DEFAULT_LAT
            origin_lng = DEFAULT_LNG

        results = []
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

        # Trier STRICTEMENT par distance d'abord pour garantir la proximité
        results.sort(key=lambda x: x.get("distance_km", 999.0))

        # Si l'utilisateur est à proximité, filtrer dans un rayon raisonnable (max_radius_km)
        close_results = [r for r in results if r["distance_km"] <= max_radius_km]
        selected = close_results[:limit] if close_results else results[:limit]

        if close_results:
            selected.sort(key=lambda x: (0 if x.get("garde") else 1, x["distance_km"]))
            selected = selected[:limit]

        # Enrichissement avec URLs d'action rapide (WhatsApp, Appel, Itinéraire Google Maps)
        enriched = []
        for p in selected:
            item = self._format_pharmacy(p)
            enriched.append(item)

        return enriched

    def _format_pharmacy(self, p: Dict, drug_name: str = "") -> Dict:
        """Standardise la fiche d'une pharmacie et génère les liens d'action directe."""
        name = p.get("title") or p.get("Nom") or "Pharmacie"
        raw_phone = str(p.get("Phone") or p.get("Tel") or "").strip()
        address = p.get("address") or p.get("Adresse") or ""
        city = p.get("Ville") or ""
        plat = p.get("lat")
        plng = p.get("lng")
        distance = p.get("distance_km", 0.0)
        is_garde = bool(p.get("garde"))

        # Nettoyage numéro marocain pour URL WhatsApp et Appel
        digits = "".join(c for c in raw_phone if c.isdigit())
        int_phone = ""
        if digits.startswith("0") and len(digits) == 10:
            int_phone = "212" + digits[1:]
        elif digits.startswith("212"):
            int_phone = digits

        # Message prérempli WhatsApp
        wa_text = f"Salam, wach dwa {drug_name} disponible 3ndkom daba ?" if drug_name else "Salam, wach l-pharmacie maftou7a daba ?"
        import urllib.parse
        encoded_msg = urllib.parse.quote_plus(wa_text)

        whatsapp_url = f"https://wa.me/{int_phone}?text={encoded_msg}" if int_phone else ""
        phone_url = f"tel:+{int_phone}" if int_phone else (f"tel:{raw_phone}" if raw_phone else "")
        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={plat},{plng}" if plat and plng else ""

        return {
            "id": p.get("id"),
            "name": name,
            "title": name,
            "phone": raw_phone,
            "Phone": raw_phone,
            "address": address,
            "city": city,
            "ville": city,
            "Ville": city,
            "is_garde": is_garde,
            "garde": p.get("garde", ""),
            "lat": plat,
            "lng": plng,
            "distance_km": distance,
            "whatsapp_url": whatsapp_url,
            "phone_url": phone_url,
            "maps_url": maps_url,
        }

# Instance singleton partagée
pharmacy_service = PharmacyService()
