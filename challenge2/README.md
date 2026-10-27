# 📷 Challenge #2 : Medication Box Recognition
### Reconnaissance de Boîtes de Médicaments par Computer Vision & OCR

**Auteurs :** Diallo Mamadou Tahirou & BenelMoudden Hassan

---

## 🎯 Objectif du Projet
Concevoir l'architecture et le pipeline technique permettant d'identifier de manière fiable un médicament à partir d'une simple photo prise par smartphone par un patient ou un soignant, dans des conditions réelles et non contrôlées (reflets plastiques, contre-jour, flou de bougé, emballages froissés).

Le défi intègre le bilinguisme systématique des packagings au Maroc (**Arabe** et **Français**).

---

## 🔬 Pipeline d'Ingénierie en 3 Phases

```
┌─────────────────┐       ┌────────────────────┐       ┌──────────────────────┐
│ 1. Vision       │       │ 2. OCR Bilingue    │       │ 3. Matching CNOPS    │
│    & RoI        │ ────> │    (Arabe / FR)    │ ────> │    & Multi-Attributs │
│ YOLOv8 + CLAHE  │       │ PaddleOCR/EasyOCR  │       │ RapidFuzz + DCI      │
└─────────────────┘       └────────────────────┘       └──────────────────────┘
```

1. **Phase 1 : Détection & Prétraitement Géométrique** :
   - Détection de la boîte via un modèle léger **YOLOv8-nano** pour extraire la zone d'intérêt (RoI).
   - Redressement de l'angle (*deskew* via Transformée de Hough).
   - Rehaussement de contraste local adaptatif (**CLAHE**) pour supprimer les reflets spéculaires et faire ressortir les caractères.

2. **Phase 2 : OCR Hybride Bilingue (Arabe & Français)** :
   - Utilisation de **PaddleOCR (PP-OCRv4)** ou **EasyOCR** (CRAFT + CRNN).
   - Gestion simultanée des graphies latines et arabes cursives avec post-traitement directionnel (BiDi et reshapeur de ligatures).

3. **Phase 3 : Appariement Hybride avec la Nomenclature Marocaine (5 918 SKUs)** :
   - Matching lexical tolérant aux fautes avec **RapidFuzz** (Token Set Ratio).
   - Validation conjointe obligatoire : **Marque** + **Dosage** (ex: *1000 mg*) + **Forme galénique** (ex: *comprimé*) pour désambiguïser les déclinaisons d'une même marque.

---

## 🛡️ Garde-fous & Sécurité

- **Score de Confiance Composite** :
  $$\text{Score} = 0.5 \times \text{Conf}_{\text{OCR}} + 0.5 \times \text{Sim}_{\text{Matching}}$$
  - $\ge 0.85$ : Validation automatique et retour de la fiche produit.
  - $[0.60, 0.85[$ : Envoi de 3 suggestions cliquables (photo + nom) pour confirmation active de l'utilisateur.
  - $< 0.60$ : Rejet propre avec message de guidage pour reprendre la photo.
- **Décharge légale obligatoire** rappelant la consultation obligatoire d'un professionnel de santé.

---

## 📄 Documents & Livrables Inclus

- `rapport_donnees_challenge2.pdf` : Rapport de cadrage technique 1 page (Données, Corpus & Pipeline TikZ).
- `memo_technique_vision.pdf` : Mémo d'ingénierie 1 page (Vision, OCR, Matching & Spécifications APIs REST).
- `pitch_explication_prof.txt` : Guide scripté mot à mot pour la soutenance orale devant le professeur (2 à 3 min).
- `data/ref-des-medicaments-cnops-2014.xlsx` : Base de vérité terrain officielle des 5 918 médicaments marocains.

---

## 🛠️ Implémentation & Code Source

Le code source complet du pipeline est disponible dans le package `challenge2/vision/` :
- `preprocessor.py` : Algorithmes de segmentation RoI, CLAHE anti-reflet et redressement d'angle (deskew).
- `ocr_engine.py` : Moteur OCR bilingue (Arabe et Français), gestion BiDi et extraction de regex posologiques.
- `matcher.py` : Moteur d'appariement RapidFuzz, boost multi-attributs (marque + dosage + forme) et calcul du score composite réglementaire.
- `service.py` : Orchestrateur end-to-end intégrant les alternatives génériques CNOPS.
- `routes.py` : 4 endpoints REST FastAPI (`POST /vision/recognize`, `POST /vision/ocr-extract`, `POST /vision/match-catalog`, `GET /catalog/drugs/{id}`).

### Exécution des Tests Automatisés
```bash
PYTHONPATH=. .venv/bin/pytest challenge2/tests/ -v
```
Les 17 tests unitaires et d'intégration couvrent la totalité du pipeline de vision, d'OCR et d'APIs.

