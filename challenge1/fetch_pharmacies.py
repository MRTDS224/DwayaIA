#!/usr/bin/env python3
"""
Script de collecte des pharmacies au Maroc via l'API saydalia.ma
Pour le Challenge #1 - Patient Pharmacy Assistance
"""

import json
import time
import urllib.request
import urllib.parse
import ssl
import os

# Configuration API sécurisée via variable d'environnement
API_URL = "https://saydalia.ma/api/siteweb_api.php"
API_KEY = os.getenv("SAYDALIA_API_KEY", "")
OUTPUT_JSON = "challenge1/data/pharmacies_maroc.json"

# Liste de coordonnées centrales des principales villes marocaines
MOROCCO_CITIES_COORDS = {
    "Agadir": (30.4278, -9.5981),
    "Casablanca_Centre": (33.5731, -7.5898),
    "Casablanca_Nord": (33.6000, -7.5300),
    "Casablanca_Sud": (33.5300, -7.6500),
    "Rabat": (34.0209, -6.8416),
    "Salé": (34.0531, -6.7985),
    "Marrakech": (31.6295, -7.9811),
    "Tanger": (35.7595, -5.8340),
    "Fès": (34.0331, -5.0003),
    "Meknès": (33.8935, -5.5473),
    "Oujda": (34.6867, -1.9114),
    "Tétouan": (35.5889, -5.3626),
    "Kénitra": (34.2610, -6.5802),
    "El Jadida": (33.2316, -8.5007),
    "Safi": (32.2994, -9.2372),
    "Nador": (35.1681, -2.9335),
    "Béni Mellal": (32.3373, -6.3498),
    "Khouribga": (32.8811, -6.9063),
    "Laâyoune": (27.1253, -13.1625),
    "Dakhla": (23.6848, -15.9579)
}

def fetch_pharmacies_for_coords(lat, lng):
    params = {
        "origin": f"{lat},{lng}",
        "limit": 50,
        "api_key": API_KEY
    }
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    )
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                return data if isinstance(data, list) else []
    except Exception as e:
        print(f"  [!] Erreur lors de la requête ({lat}, {lng}): {e}")
    return []

def main():
    print("=======================================================")
    print(" Collecte des données des Pharmacies - saydalia.ma API")
    print("=======================================================\n")

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    all_pharmacies = {}
    garde_count = 0

    for city_name, (lat, lng) in MOROCCO_CITIES_COORDS.items():
        print(f"[*] Interrogation pour la zone: {city_name:20s} (Lat: {lat}, Lng: {lng})...")
        results = fetch_pharmacies_for_coords(lat, lng)
        print(f"    -> Récupérés: {len(results)} pharmacies")
        
        for item in results:
            item_id = item.get("id")
            if item_id and item_id not in all_pharmacies:
                all_pharmacies[item_id] = item
                if item.get("garde"):
                    garde_count += 1
        
        time.sleep(0.3) # Respect de la charge serveur

    pharmacy_list = list(all_pharmacies.values())

    print("\n-------------------------------------------------------")
    print(f"[✓] Total Pharmacies uniques collectées : {len(pharmacy_list)}")
    print(f"[✓] Pharmacies de garde identifiées      : {garde_count}")
    print("-------------------------------------------------------")

    # Sauvegarde en JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(pharmacy_list, f, ensure_ascii=False, indent=2)

    print(f"[✓] Données sauvegardées avec succès dans: {OUTPUT_JSON}\n")

if __name__ == "__main__":
    main()

