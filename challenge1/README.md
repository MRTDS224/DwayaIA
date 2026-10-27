# 💊 Challenge #1 : Dwaya AI (دوايا)
### Assistant Conversationnel Multilingue Patient-Pharmacie (Maroc)

**Auteurs :** Diallo Mamadou Tahirou & BenelMoudden Hassan

---

## 🎯 Objectif du Projet
Développer un service intelligent capable d'assister les usagers au Maroc dans leurs requêtes pharmaceutiques textuelles ou vocales :
- Prise en charge du trilinguisme et du code-switching : **Darija (caractères arabes)**, **Arabizi (chiffres 3, 7, 9)** et **Français**.
- Résolution floue des fautes d'orthographe sur les médicaments contre la base officielle **CNOPS/DMP (5 918 produits)**.
- Localisation spatiale des **800 pharmacies marocaines** avec identification des officines **de garde 24h/24**.
- Interface moderne avec **carte interactive OpenStreetMap**, **synthèse vocale naturelle (TTS)** et **enregistrement microphone universel**.

---

## 🧱 Architecture des Modules

```text
challenge1/
├── app/
│   ├── config.py                 # Configuration globale et constantes
│   ├── main.py                   # Serveur FastAPI, routes REST et point d'entrée UI
│   ├── core/
│   │   ├── normalizer.py         # Mappage Arabizi, suppression tashkeel arabe et accents français
│   │   └── nlu_engine.py         # Classification des 5 intents + extraction conjointe NER + SAMU 150
│   ├── services/
│   │   ├── catalog_service.py    # Algorithme RapidFuzz sur les 5 918 médicaments CNOPS + génériques DCI
│   │   ├── pharmacy_service.py   # Calcul géodésique Haversine & filtrage de proximité (<35km)
│   │   └── audio_service.py      # Synthèse vocale gTTS (ar/fr) & transcription audio MediaRecorder
│   ├── models/
│   │   └── schemas.py            # Modèles Pydantic pour validation et OpenAPI Swagger
│   └── static/
│       ├── index.html            # Web SPA : Chatbot (gauche) + Carte & Inspecteur NLU (droite)
│       └── app.js                # Interaction frontend, Leaflet.js, TTS et MediaRecorder
│
├── data/
│   ├── ref-des-medicaments-cnops-2014.xlsx  # Catalogue officiel des médicaments marocains
│   └── pharmacies_maroc.json               # 800 pharmacies réelles avec statut de garde
│
├── tests/
│   ├── test_normalizer.py        # Tests unitaires de translittération
│   ├── test_matcher.py           # Tests de fuzzy matching tolérant aux fautes
│   ├── test_nlu.py               # Tests de classification d'intentions et d'urgences
│   └── test_api.py               # Tests d'intégration des endpoints FastAPI
│
├── rapport_donnees_challenge1.pdf# Rapport de cadrage 1 page (Données & Architecture)
├── memo_technique_nlp.pdf        # Mémo technique d'ingénierie 1 page
├── presentation_slides.pdf       # Support de soutenance Beamer 16:9 (4 diapositives)
└── presentation_slides.tex       # Source LaTeX Beamer
```

---

## 🛠️ Endpoints REST Disponibles (`/api/*` & `/vision/*`)

| Méthode | Route | Description |
| :--- | :--- | :--- |
| `POST` | `/api/chat` | **Orchestrateur tout-en-un** : analyse NLU, résolution CNOPS, pharmacies proches et formulation de réponse. |
| `POST` | `/api/nlu/parse` | Analyse textuelle brute : extrait l'intention, les entités et le score de confiance. |
| `POST` | `/api/catalog/search` | Recherche floue tolérante aux fautes dans le catalogue CNOPS. |
| `GET` | `/api/catalog/drugs/{cip_code}` | Fiche produit exhaustive (PPV, DCI, forme galénique, remboursement AMO). |
| `GET` | `/api/catalog/drugs/{cip_code}/alternatives` | Recherche des génériques et équivalents thérapeutiques par DCI. |
| `POST` | `/api/pharmacies/availability` | Localisation d'officines proches et de garde par coordonnées GPS ou ville. |
| `POST` | `/api/audio/tts` | Synthèse vocale haute fidélité (retourne un flux audio MP3 naturel). |
| `POST` | `/api/audio/transcribe` | Transcription d'un fichier audio enregistré depuis le micro navigateur. |
| `POST` | `/vision/recognize` | Reconnaissance visuelle de boîte par photo/upload (RoI, CLAHE, OCR bilingue et matching CNOPS). |

---

## 🧪 Exécution des Tests

```bash
PYTHONPATH=. .venv/bin/pytest challenge1/tests/ -v
```

---

## 💬 Exemples de Requêtes Utilisateurs Supportées

1. **Disponibilité & Officines proches** :
   - *"Khassni doliprane 1g 3afak ana f agadir"*
   - *"Fin nqder nlqa doli sirop f casablanca ?"*
2. **Prix & Remboursement CNOPS/AMO** :
   - *"Chhal taman dial augmentin 1g wa wach remboursable cnops ?"*
   - *"Prix du kardegic 75 svp"*
3. **Génériques & Substitution DCI** :
   - *"Malqitch clamoxyl 1g bghit chi générique f blastou"*
4. **Pharmacies de garde seules** :
   - *"Pharmacie de garde casablanca daba"*
5. **Garde-fou d'Urgence Médicale** :
   - *"3andi wja3 f sadri bzaf w tkhneqt"* ➔ Déclenchement automatique de l'alerte SAMU 150 / 141.

