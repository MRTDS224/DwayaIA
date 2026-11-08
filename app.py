"""
Point d'entrée pour le déploiement Hugging Face Spaces (SDK Gradio / FastAPI).
Hugging Face attend un fichier 'app.py' à la racine et le lance sur le port 7860.
"""
import os
import uvicorn
from challenge1.app.main import app as fastapi_app

# Port par défaut imposé par Hugging Face Spaces : 7860
PORT = int(os.environ.get("PORT", 7860))

# Export pour les runners ASGI
app = fastapi_app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
