# 🏥 Healthcare AI Challenges (Morocco)

Ce dépôt regroupe les travaux d'ingénierie et d'implémentation réalisés dans le cadre des **Challenges en e-Santé et Intelligence Artificielle au Maroc**.

**Binôme :**
- **Diallo Mamadou Tahirou**
- **BenelMoudden Hassan**

---

## 📂 Structure du Dépôt (Monorepo)

```text
challenge/
├── challenge1/               # Challenge #1 : Dwaya AI (Assistant Pharmacie Multilingue)
│   ├── app/                  # Backend FastAPI, Pipeline NLU, Matching & Services Vocaux
│   ├── data/                 # Référentiel CNOPS (5 918 médicaments) & Pharmacies (800 officines)
│   ├── tests/                # Suite complète de tests automatisés (pytest)
│   ├── rapport_donnees_challenge1.pdf  # Rapport de cadrage technique (1 page)
│   └── memo_technique_nlp.pdf          # Mémo d'ingénierie NLP & APIs (1 page)
│
├── challenge2/               # Challenge #2 : Computer Vision & OCR Boîtes Médicaments
│   ├── data/                 # Nomenclature officielle de vérité terrain
│   ├── rapport_donnees_challenge2.pdf  # Rapport de cadrage Vision & Données (1 page)
│   ├── memo_technique_vision.pdf       # Mémo d'ingénierie Vision, OCR & Matching (1 page)
│   └── pitch_explication_prof.txt      # Guide de présentation orale pour la soutenance
│
├── requirements.txt          # Dépendances Python unifiées
└── README.md                 # Vue d'ensemble du projet
```

---

## 🚀 Démarrage Rapide

### 1. Prérequis
- Python 3.12+
- Gestionnaire d'environnement moderne **`uv`** (ou standard `venv`)
- Outil audio système : `ffmpeg`

### 2. Installation de l'environnement virtuel avec `uv`
```bash
# Création de l'environnement virtuel Python 3.12
uv venv --python 3.12 .venv

# Activation
source .venv/bin/activate

# Installation des dépendances
uv pip install -r requirements.txt
```

### 3. Lancement de Dwaya AI (Challenge #1)
```bash
PYTHONPATH=. .venv/bin/uvicorn challenge1.app.main:app --reload --port 8000
```
- 💬 **Interface Web Interactive** : [http://localhost:8000](http://localhost:8000)
- 📖 **Documentation Swagger des APIs** : [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Lancement des Tests Automatisés
```bash
PYTHONPATH=. .venv/bin/pytest challenge1/tests/
```
*(15 tests unitaires et d'intégration validés à 100 %)*

---

## 📋 Synthèse des Challenges

| Challenge | Thématique | Technologies Clés | Livrables Disponibles |
| :--- | :--- | :--- | :--- |
| **#1 : Dwaya AI** | Assistant vocal & textuel en Darija, Arabizi et Français pour patients et pharmacies. | FastAPI, RapidFuzz, NLU Hybride, Leaflet.js, gTTS & MediaRecorder. | App Web complète, API REST, suite de tests, rapports PDF. |
| **#2 : Vision & OCR** | Détection et reconnaissance de boîtes de médicaments bilingues (Arabe/FR). | YOLOv8, CLAHE, Deskew, PaddleOCR / EasyOCR, RapidFuzz Matching. | Cadrage technique, modélisation de pipeline, mémo d'ingénierie PDF. |
