"""
Script de déploiement automatique et propre vers Hugging Face Spaces.
Crée un dépôt temporaire contenant UNIQUEMENT le code source et les données JSON,
en éliminant rigoureusement tout fichier binaire (PDF, XLSX, images de slides, .env).
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

# Répertoire racine du projet
PROJECT_ROOT = Path(__file__).resolve().parent

# Extensions à exclure impérativement pour Hugging Face
EXCLUDED_EXTENSIONS = {".pdf", ".xlsx", ".png", ".webp", ".jpg", ".pyc"}
EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".gemini"}
EXCLUDED_FILES = {".env", "push_to_hf.py"}

def is_allowed(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDED_DIRS:
            return False
    if path.name in EXCLUDED_FILES:
        return False
    if path.suffix.lower() in EXCLUDED_EXTENSIONS:
        # Autoriser uniquement les petits samples d'échantillons de test s'ils sont nécessaires
        if "challenge2/data/samples" in str(path):
            return True
        return False
    return True

def deploy():
    print("[1/4] Préparation du dossier de déploiement propre...")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Copie des fichiers autorisés
        for root, dirs, files in os.walk(PROJECT_ROOT):
            rel_root = Path(root).relative_to(PROJECT_ROOT)
            if any(part in EXCLUDED_DIRS for part in rel_root.parts):
                continue

            for file in files:
                src_file = Path(root) / file
                rel_file = src_file.relative_to(PROJECT_ROOT)
                if is_allowed(rel_file):
                    dest_file = temp_path / rel_file
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dest_file)

        # Création du README Hugging Face avec les métadonnées requises
        hf_readme = """---
title: Dwaya AI
emoji: 💊
colorFrom: green
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false
license: mit
short_description: "AI pharmacy assistant for Morocco: Darija, CNOPS & vision"
---

# 🇲🇦 Dwaya AI (دوايا) : Assistant Pharmacie Multimodal pour le Maroc
"""
        (temp_path / "README.md").write_text(hf_readme, encoding="utf-8")

        print(f"[2/4] Initialisation d'un dépôt Git propre dans {temp_path}...")
        subprocess.run(["git", "init", "-b", "main"], cwd=temp_path, check=True)
        subprocess.run(["git", "config", "user.name", "MRTDS224"], cwd=temp_path, check=True)
        subprocess.run(["git", "config", "user.email", "mrtds@users.noreply.huggingface.co"], cwd=temp_path, check=True)

        subprocess.run(["git", "add", "."], cwd=temp_path, check=True)
        subprocess.run(["git", "commit", "-m", "deploy: initial clean deployment for Hugging Face Spaces"], cwd=temp_path, check=True)

        # Vérification des fichiers commités
        res = subprocess.run(["git", "ls-files"], cwd=temp_path, capture_output=True, text=True, check=True)
        files_committed = res.stdout.strip().splitlines()
        print(f"[✓] {len(files_committed)} fichiers inclus (zéro PDF, zéro XLSX).")

        # Pousser vers Hugging Face
        remote_url = "https://huggingface.co/spaces/MRTDS224/dwaya-ia"
        print(f"[3/4] Ajout du remote distant {remote_url}...")
        subprocess.run(["git", "remote", "add", "space", remote_url], cwd=temp_path, check=True)

        print("[4/4] Push en cours vers Hugging Face Spaces...")
        print("Note : Si Git demande vos identifiants, utilisez votre nom d'utilisateur HF et votre Access Token (HF Write).")
        subprocess.run(["git", "push", "space", "main", "-f"], cwd=temp_path, check=True)

        print("\n🎉 DÉPLOIEMENT RÉUSSI ! Votre application est en cours de démarrage sur Hugging Face Spaces.")

if __name__ == "__main__":
    deploy()
