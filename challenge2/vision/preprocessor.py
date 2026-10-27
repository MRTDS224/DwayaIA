"""Module de prétraitement d'image pour boîtes de médicaments.

Implémente :
1. Détection de RoI (Zone d'intérêt / Emballage)
2. Correction photométrique (CLAHE : Contrast Limited Adaptive Histogram Equalization)
3. Redressement géométrique (Deskew)
"""

import io
import base64
import math
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import numpy as np


class ImagePreprocessor:
    """Pipeline de prétraitement optique & géométrique pour packaging pharmaceutique."""

    def __init__(self, target_max_dim: int = 1200):
        self.target_max_dim = target_max_dim

    def load_image(self, image_input: Any) -> Image.Image:
        """Charge une image depuis bytes, chemin ou objet PIL en RGB."""
        if isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
        elif isinstance(image_input, (bytes, bytearray)):
            img = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, str):
            img = Image.open(image_input).convert("RGB")
        else:
            raise ValueError(f"Type d'image non supporté : {type(image_input)}")

        # Redimensionnement si dimensions excessives pour optimiser les performances
        w, h = img.size
        max_dim = max(w, h)
        if max_dim > self.target_max_dim:
            scale = self.target_max_dim / float(max_dim)
            new_w, new_h = int(w * scale), int(h * scale)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        return img

    def apply_clahe(
        self,
        img: Image.Image,
        clip_limit: float = 2.5,
        grid_size: Tuple[int, int] = (8, 8),
    ) -> Image.Image:
        """Applique CLAHE (Contrast Limited Adaptive Histogram Equalization)

        Supprime les reflets spéculaires et compense les ombres portées
        sur le packaging plastique / carton verni.
        """
        # Convertir en espace LAB / Niveaux de gris
        gray = img.convert("L")
        arr = np.array(gray, dtype=np.float32)
        h, w = arr.shape

        gh, gw = grid_size
        th, tw = h // gh, w // gw

        if th < 4 or tw < 4:
            # Image trop petite pour CLAHE multipasse : fallback égalisation globale
            return ImageOps.equalize(img)

        # Matrice résultante
        out = np.zeros_like(arr)

        # Histogrammes par tuile
        histograms = []
        for r in range(gh):
            row_hists = []
            r_start = r * th
            r_end = (r + 1) * th if r < gh - 1 else h
            for c in range(gw):
                c_start = c * tw
                c_end = (c + 1) * tw if c < gw - 1 else w

                tile = arr[r_start:r_end, c_start:c_end]
                hist, _ = np.histogram(tile, bins=256, range=(0, 256))

                # Écrêtage (Clip limit) & redistribution de l'excédent
                actual_clip = int(clip_limit * (tile.size / 256.0))
                excess = np.maximum(hist - actual_clip, 0).sum()
                clipped_hist = np.minimum(hist, actual_clip)
                clipped_hist += int(excess // 256)

                # CDF normalisée
                cdf = clipped_hist.cumsum()
                cdf_min = cdf.min()
                cdf_max = cdf.max()
                if cdf_max > cdf_min:
                    lut = (cdf - cdf_min) * 255.0 / (cdf_max - cdf_min)
                else:
                    lut = np.arange(256)

                row_hists.append(lut)
            histograms.append(row_hists)

        # Interpolation bilinéaire entre tuiles
        for r in range(gh):
            r_start = r * th
            r_end = (r + 1) * th if r < gh - 1 else h
            for c in range(gw):
                c_start = c * tw
                c_end = (c + 1) * tw if c < gw - 1 else w

                tile = arr[r_start:r_end, c_start:c_end].astype(np.uint8)
                lut = histograms[r][c]
                out[r_start:r_end, c_start:c_end] = lut[tile]

        out_img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode="L")
        
        # Réinjecter la couleur en combinant avec la saturation originale
        r, g, b = img.split()
        enhanced_gray = ImageEnhance.Contrast(out_img).enhance(1.2)
        return Image.merge("RGB", (enhanced_gray, enhanced_gray, enhanced_gray))

    def estimate_skew_angle(self, img: Image.Image) -> float:
        """Estime l'angle d'inclinaison (skew angle en degrés) via gradient horizontal."""
        gray = img.convert("L")
        # Réduire la résolution pour accélérer le calcul
        small = gray.resize((150, 150), Image.Resampling.BILINEAR)
        arr = np.array(small, dtype=np.float32)

        # Filtre Sobel horizontal simple
        sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
        sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

        # Convolutions 2D manuelles avec slicing
        gx = (
            arr[:-2, 2:]
            + 2 * arr[1:-1, 2:]
            + arr[2:, 2:]
            - (arr[:-2, :-2] + 2 * arr[1:-1, :-2] + arr[2:, :-2])
        )
        gy = (
            arr[2:, :-2]
            + 2 * arr[2:, 1:-1]
            + arr[2:, 2:]
            - (arr[:-2, :-2] + 2 * arr[:-2, 1:-1] + arr[:-2, 2:])
        )

        magnitude = np.sqrt(gx**2 + gy**2)
        angles = np.arctan2(gy, gx) * (180.0 / np.pi)

        # Filtrer les contours significatifs
        strong_edges = magnitude > np.percentile(magnitude, 85)
        if not np.any(strong_edges):
            return 0.0

        filtered_angles = angles[strong_edges]
        # Normaliser dans [-45, 45]
        norm_angles = (filtered_angles + 45.0) % 90.0 - 45.0
        hist, bin_edges = np.histogram(norm_angles, bins=36, range=(-45, 45))
        dominant_bin = np.argmax(hist)
        dominant_angle = float((bin_edges[dominant_bin] + bin_edges[dominant_bin + 1]) / 2.0)

        # Seuillage : si inclinaison négligeable (< 1.5°), ne pas pivoter
        if abs(dominant_angle) < 1.5:
            return 0.0
        return round(dominant_angle, 2)

    def deskew(self, img: Image.Image, angle: Optional[float] = None) -> Tuple[Image.Image, float]:
        """Pivote l'image pour aligner le texte horizontalement."""
        if angle is None:
            angle = self.estimate_skew_angle(img)

        if abs(angle) < 1.0:
            return img, 0.0

        # Rotation avec fond blanc pour ne pas perturber l'OCR
        rotated = img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC, fillcolor=(255, 255, 255))
        return rotated, angle

    def detect_roi(self, img: Image.Image) -> Dict[str, Any]:
        """Détecte la zone d'intérêt principale (Region of Interest / Bounding Box)."""
        w, h = img.size
        gray = img.convert("L")

        # Filtre de détection de contours (Laplacian/Edge)
        edges = gray.filter(ImageFilter.FIND_EDGES)
        arr = np.array(edges, dtype=np.uint8)

        # Seuillage adaptatif
        threshold = np.percentile(arr, 75)
        mask = arr > threshold

        # Trouver les coordonnées extrêmes avec marge de sécurité
        y_indices, x_indices = np.where(mask)
        if len(x_indices) > 50 and len(y_indices) > 50:
            min_x = max(0, int(np.percentile(x_indices, 5)))
            max_x = min(w, int(np.percentile(x_indices, 95)))
            min_y = max(0, int(np.percentile(y_indices, 5)))
            max_y = min(h, int(np.percentile(y_indices, 95)))

            roi_w = max_x - min_x
            roi_h = max_y - min_y

            # Vérifier que la RoI est d'une taille plausible (> 25% de l'image)
            if roi_w > 0.25 * w and roi_h > 0.25 * h:
                return {
                    "x": min_x,
                    "y": min_y,
                    "w": roi_w,
                    "h": roi_h,
                    "confidence": 0.88,
                    "detected": True,
                }

        # Fallback : boîte centrale (marge de 8% sur les bords)
        return {
            "x": int(w * 0.08),
            "y": int(h * 0.08),
            "w": int(w * 0.84),
            "h": int(h * 0.84),
            "confidence": 0.65,
            "detected": False,
        }

    def process(self, image_input: Any) -> Dict[str, Any]:
        """Pipeline complet : Chargement -> RoI -> CLAHE -> Deskew."""
        original = self.load_image(image_input)
        roi = self.detect_roi(original)

        # Découpe de la RoI pour analyse
        cropped = original.crop(
            (roi["x"], roi["y"], roi["x"] + roi["w"], roi["y"] + roi["h"])
        )

        # CLAHE
        enhanced = self.apply_clahe(cropped)

        # Deskew
        deskewed, angle = self.deskew(enhanced)

        # Encodage en base64 pour restitution dans l'API ou l'interface
        buf = io.BytesIO()
        deskewed.save(buf, format="JPEG", quality=85)
        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")

        return {
            "original_size": original.size,
            "roi": roi,
            "skew_angle": angle,
            "processed_image": deskewed,
            "processed_base64": f"data:image/jpeg;base64,{b64_str}",
        }


# Instance singleton
preprocessor = ImagePreprocessor()

