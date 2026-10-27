"""Service LLM Gemini Hybride pour Dwaya AI (SaydaliaBot).

Gère :
1. Compréhension multimodale de haute fidélité (texte + photo de boîte).
2. Dialogue naturel et empathique en Darija marocaine (arabe et Arabizi) et Français.
3. Grounding strict CNOPS (prix réglementés au dirham, DCI, génériques marocains).
4. Orientation vers les pharmacies de garde les plus proches.
5. Garde-fous médicaux stricts (urgences 141/15, rappel systématique du médecin).
6. Fallback gracieux vers le moteur déterministe local en cas d'absence de clé ou d'erreur réseau.
"""

import os
import io
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image

# Import des services métiers locaux pour le grounding
from challenge1.app.services.catalog_service import catalog_service
from challenge1.app.services.pharmacy_service import pharmacy_service

# Chargement sécurisé des variables d'environnement (.env local)
def _load_env_safely():
    env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("\"").strip("'")
                    os.environ.setdefault(k, v)
        except Exception:
            pass

_load_env_safely()

PREFERRED_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
]

SYSTEM_PROMPT = """Tu es Dwaya AI (SaydaliaBot), l'assistant virtuel intelligent de référence pour l'orientation pharmaceutique au Maroc.
Tu aides les citoyens marocains avec bienveillance, clarté et précision médicale.

Tes compétences linguistiques :
- Tu t'exprimes avec fluidité naturelle en DARIJA MAROCAINE (aussi bien en alphabet arabe 'دارجة' qu'en Arabizi avec les chiffres 3, 7, 9) si l'utilisateur te parle en Darija.
- Tu réponds en FRANÇAIS si l'utilisateur s'adresse à toi en Français.

RÈGLES D'OR DE SÉCURITÉ MÉDICALE :
1. Tu n'es PAS un médecin et tu ne poses AUCUN diagnostic médical autonome.
2. Si l'utilisateur mentionne des symptômes graves d'URGENCE (douleur thoracique irradiante, convulsion, perte de connaissance, détresse respiratoire aiguë, empoisonnement), alerte IMMÉDIATEMENT d'appeler le SAMU (141) ou la Protection Civile (15).
3. Pour les prix et les médicaments : tu t'appuies STRICTEMENT sur le catalogue officiel marocain (CNOPS). N'invente jamais un prix de médicament.
4. Encourage toujours la consultation d'un médecin ou d'un pharmacien avant la prise d'un médicament, particulièrement pour les femmes enceintes, enfants et personnes âgées.
5. Sois concis, direct et structure ta réponse avec des puces pour être très lisible sur smartphone."""


class GeminiService:
    """Orchestrateur Gemini pour le chat multimodal et conversationnel en Darija."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialise le client Google GenAI si la clé est disponible."""
        if not self.api_key:
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            print(f"[!] Impossible d'initialiser le client Google GenAI: {e}")
            self.client = None

    @property
    def is_available(self) -> bool:
        """Indique si le service Gemini est opérationnel."""
        return self.client is not None and bool(self.api_key)

    def generate_multimodal_reply(
        self,
        user_message: str,
        image_bytes: Optional[bytes] = None,
        image_mime: str = "image/jpeg",
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None,
        detected_drug: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Génère une réponse intelligente combinant texte, image et outils réglementaires."""
        # 1. Préparation du contexte d'ancrage CNOPS et Pharmacies
        grounding_context = self._build_grounding_context(user_message, detected_drug, user_lat, user_lon)

        # 2. Si Gemini n'est pas disponible, bascule immédiate sur le moteur local
        if not self.is_available:
            return self._fallback_local_response(user_message, detected_drug, grounding_context)

        # 3. Construction des contenus multimodaux pour Gemini
        contents: List[Any] = []

        # Ajout de l'image si fournie
        if image_bytes:
            try:
                pil_img = Image.open(io.BytesIO(image_bytes))
                contents.append(pil_img)
            except Exception as e:
                print(f"[!] Erreur ouverture image pour Gemini: {e}")

        # Prompt enrichi avec le grounding réglementaire
        prompt_parts = []
        if grounding_context.get("drug_summary"):
            prompt_parts.append(f"[DONNÉES OFFICIELLES CNOPS DÉTECTÉES EN BASE]\n{grounding_context['drug_summary']}\n")

        if grounding_context.get("pharmacies_summary"):
            prompt_parts.append(f"[PHARMACIES DE GARDE / PROCHES DISPONIBLES]\n{grounding_context['pharmacies_summary']}\n")

        user_prompt = user_message.strip() if user_message else "Peux-tu analyser cette boîte de médicament et m'expliquer ce que c'est en Darija ?"
        prompt_parts.append(f"Message de l'utilisateur : {user_prompt}")

        contents.append("\n".join(prompt_parts))

        # 4. Appel avec gestion des modèles prioritaires
        for model_name in PREFERRED_MODELS:
            try:
                from google.genai import types
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.4,
                    )
                )
                reply_text = response.text.strip() if response and response.text else ""
                if reply_text:
                    return {
                        "text": reply_text,
                        "model_used": model_name,
                        "matched_drug": detected_drug or grounding_context.get("drug_obj"),
                        "pharmacies": grounding_context.get("pharmacies_list", []),
                        "is_llm": True,
                    }
            except Exception as e:
                print(f"[!] Erreur appel Gemini ({model_name}): {e}")
                continue

        # 5. En cas d'échec de tous les modèles distants, fallback transparent
        return self._fallback_local_response(user_message, detected_drug, grounding_context)

    def _build_grounding_context(
        self,
        user_message: str,
        detected_drug: Optional[Dict],
        user_lat: Optional[float],
        user_lon: Optional[float],
    ) -> Dict[str, Any]:
        """Extrait les faits vérifiés du catalogue CNOPS et de l'annuaire des pharmacies."""
        ctx: Dict[str, Any] = {
            "drug_summary": "",
            "drug_obj": None,
            "pharmacies_summary": "",
            "pharmacies_list": [],
        }

        # Données médicament
        drug = detected_drug
        if not drug and user_message:
            # Recherche CNOPS locale rapide
            search_res = catalog_service.search(user_message, limit=1)
            if search_res:
                drug = search_res[0]

        if drug:
            ctx["drug_obj"] = drug
            nom = drug.get("nom", "")
            dci = drug.get("dci", "")
            ppv = drug.get("ppv", 0.0)
            dosage = drug.get("dosage", "")
            forme = drug.get("forme", "")
            is_gen = drug.get("is_generique", False)
            generiques = catalog_service.get_alternatives(dci) if dci else []
            gen_names = [f"{g.get('nom')} ({g.get('ppv')} DH)" for g in generiques[:3]]

            lines = [
                f"- Nom : {nom}",
                f"- DCI (Matière active) : {dci}",
                f"- Dosage & Forme : {dosage} | {forme}",
                f"- Prix Public Maroc (PPV) : {ppv} MAD (Dirhams)",
                f"- Statut : {'Générique' if is_gen else 'Princeps'}",
            ]
            if gen_names:
                lines.append(f"- Exemples d'alternatives génériques moins chères au Maroc : {', '.join(gen_names)}")
            ctx["drug_summary"] = "\n".join(lines)

        # Données pharmacies (proximité / garde)
        # Détection de ville dans le message si coordonnées non fournies
        detected_city = None
        if user_message:
            for city in ["casablanca", "casa", "rabat", "fes", "tanger", "marrakech", "agadir", "meknes", "oujda", "kenitra"]:
                if city in user_message.lower():
                    detected_city = "Casablanca" if city == "casa" else city.capitalize()
                    break

        pharms = pharmacy_service.search_nearby(
            lat=user_lat,
            lng=user_lon,
            city=detected_city,
            limit=3
        )
        if pharms:
            ctx["pharmacies_list"] = pharms
            p_lines = []
            for p in pharms:
                dist_str = f" (~{p.get('distance_km')} km)" if p.get('distance_km', 999) < 100 else ""
                garde_str = " [DE GARDE]" if p.get("is_garde") else ""
                p_lines.append(f"- {p.get('name')} à {p.get('city')}{garde_str}{dist_str} | Tél: {p.get('phone')}")
            ctx["pharmacies_summary"] = "\n".join(p_lines)

        return ctx

    def _fallback_local_response(
        self,
        user_message: str,
        detected_drug: Optional[Dict],
        grounding_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Réponse déterministe locale de secours si Gemini n'est pas configuré ou indisponible."""
        drug = detected_drug or grounding_context.get("drug_obj")
        drug_name = drug.get("nom", "") if drug else ""
        ppv = drug.get("ppv", "") if drug else ""

        if drug:
            text = f"Salam! Lqit dwa **{drug_name}**.\n- Prix public officiel (PPV) : **{ppv} MAD**.\n- DCI : {drug.get('dci', 'Non spécifiée')}.\n"
            if grounding_context.get("pharmacies_list"):
                text += "\nHna l-pharmacies li qrab lik bach tswl 3lih :"
        else:
            text = "Salam! Dwaya AI f l-khidma dyalk. Tqder tswlni 3la ay dwa f l-Maghrib, taman dyalo, les génériques dyalo, wla l-pharmacies de garde li qrab lik."

        return {
            "text": text,
            "model_used": "local-fallback",
            "matched_drug": drug,
            "pharmacies": grounding_context.get("pharmacies_list", []),
            "is_llm": False,
        }


# Instance singleton
gemini_service = GeminiService()
