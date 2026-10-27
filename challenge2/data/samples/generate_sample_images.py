"""Générateur d'échantillons de packaging pour les tests du Challenge #2.

Crée des images de test avec graphies bilingues et typographies réelles.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os

SAMPLES_DIR = Path(__file__).resolve().parent

def get_font(size=24, bold=False):
    font_candidates = [
        "/usr/share/fonts/google-carlito-fonts/Carlito-Bold.ttf" if bold else "/usr/share/fonts/google-carlito-fonts/Carlito-Regular.ttf",
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
        "/usr/share/fonts/adwaita-sans-fonts/AdwaitaSans-Regular.ttf",
    ]
    for p in font_candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def create_box_image(
    filename: str,
    brand: str,
    dci: str,
    dosage: str,
    form: str,
    brand_color=(25, 95, 170),
    accent_color=(220, 38, 38),
    arabic_brand="",
):
    img = Image.new("RGB", (800, 520), color=(248, 249, 250))
    draw = ImageDraw.Draw(img)

    title_font = get_font(size=44, bold=True)
    sub_font = get_font(size=26, bold=True)
    body_font = get_font(size=20, bold=False)
    small_font = get_font(size=16, bold=False)

    # Boîte 3D contour
    draw.rectangle([40, 30, 760, 480], fill=(255, 255, 255), outline=(190, 200, 210), width=3)

    # Bandeau supérieur
    draw.rectangle([40, 30, 760, 130], fill=brand_color)

    # Titre de marque
    draw.text((60, 50), brand, fill=(255, 255, 255), font=title_font)
    if arabic_brand:
        draw.text((500, 50), arabic_brand, fill=(255, 255, 255), font=title_font)

    # DCI et Dosage
    draw.text((60, 160), dci, fill=brand_color, font=sub_font)
    draw.text((60, 220), dosage, fill=accent_color, font=title_font)
    draw.text((60, 290), form, fill=(60, 70, 80), font=body_font)

    # Informations fabricant et lot
    draw.text((60, 410), "Usage oral - Tenir hors de portee des enfants", fill=(120, 130, 140), font=small_font)
    draw.text((60, 440), "CIP CNOPS Maroc | Lot : MA-2026-X", fill=(140, 150, 160), font=small_font)

    out_path = SAMPLES_DIR / filename
    img.save(out_path, format="JPEG", quality=95)
    print(f"[✓] Image générée : {out_path}")
    return out_path


if __name__ == "__main__":
    create_box_image(
        "augmentin_1g.jpg",
        brand="AUGMENTIN",
        dci="Amoxicilline / Acide clavulanique",
        dosage="1 g / 125 mg",
        form="Poudre pour suspension buvable en sachet",
        brand_color=(20, 80, 160),
        accent_color=(210, 40, 40),
        arabic_brand="أوغمنتين",
    )
    create_box_image(
        "kardegic_75mg.jpg",
        brand="KARDEGIC",
        dci="Acétylsalicylate de lysine",
        dosage="75 mg",
        form="Poudre pour solution buvable en sachet",
        brand_color=(15, 118, 110),
        accent_color=(37, 99, 235),
        arabic_brand="كارديجيك",
    )
    create_box_image(
        "clamoxyl_500mg.jpg",
        brand="CLAMOXYL",
        dci="Amoxicilline",
        dosage="500 mg",
        form="Gélules - Boîte de 16",
        brand_color=(180, 83, 9),
        accent_color=(220, 38, 38),
        arabic_brand="كلاموكسيل",
    )
