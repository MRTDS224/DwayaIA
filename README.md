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
│   ├── presentation_slides.pdf # Présentation visuelle Beamer 16:9 (4 diapositives)
│   ├── rapport_donnees_challenge1.pdf  # Rapport de cadrage technique (1 page)
│   └── memo_technique_nlp.pdf          # Mémo d'ingénierie NLP & APIs (1 page)
│
├── challenge2/               # Challenge #2 : Computer Vision & OCR Boîtes Médicaments
│   ├── vision/               # Pipeline Vision : CLAHE, Deskew, OCR Bilingue & Matching
│   ├── tests/                # 17 tests unitaires et d'intégration (Vision, OCR, APIs)
│   ├── data/                 # Nomenclature officielle CNOPS de vérité terrain
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

### 3. Lancement de Dwaya AI (Plateforme Multimodale)
```bash
PYTHONPATH=. .venv/bin/uvicorn challenge1.app.main:app --reload --port 8000
```
- 💬 **Interface Web Interactive (Texte, Voix & Scan Caméra)** : [http://localhost:8000](http://localhost:8000)
- 📖 **Documentation Swagger des APIs (Challenge 1 & 2)** : [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Lancement de la Suite Complète de Tests Automatisés
```bash
PYTHONPATH=. .venv/bin/pytest -v
```
*(**32 tests validés à 100 %** : 15 tests pour Challenge #1 et 17 tests pour Challenge #2)*

---

## 📊 Support de Présentation (Soutenance)

Le support de présentation de soutenance en **4 slides visuelles (LaTeX Beamer 16:9 Widescreen)** est disponible :
- 📄 **PDF Projetable** : `challenge1/presentation_slides.pdf`
- 📝 **Code Source LaTeX** : `challenge1/presentation_slides.tex`
- Contenu :
  1. *Identité & Chiffres Clés* (5 918 CNOPS, 800 pharmacies, 3 langues, vocal + carte Leaflet).
  2. *Réalités Terrain Maroc vs Notre Réponse d'Ingénierie* (Arabizi, fautes, gardes de nuit, canal vocal).
  3. *Architecture du Pipeline & Garde-fou Médical* (SAMU 150).
  4. *Périmètre Opérationnel : Ce que Dwaya AI fait vs ce qu'il ne fait pas*.

---

## 📋 Synthèse des Challenges

| Challenge | Thématique | Technologies Clés | Statut & Livrables |
| :--- | :--- | :--- | :--- |
| **#1 : Dwaya AI** | Assistant vocal & textuel en Darija, Arabizi et Français pour patients et pharmacies. | FastAPI, RapidFuzz, NLU Hybride, Leaflet.js, gTTS & MediaRecorder. | **Implémenté & Fonctionnel** (App Web SPA, API REST, 15 tests pytest, slides Beamer). |
| **#2 : Vision & OCR** | Détection et reconnaissance de boîtes de médicaments bilingues (Arabe/FR). | Prétraitement CLAHE, Deskew, RoI, OCR Bilingue, RapidFuzz Multi-Attributs. | **Implémenté & Intégré** (Bouton Scan Caméra dans Dwaya AI, 4 endpoints REST, 17 tests pytest, mémo PDF). |

