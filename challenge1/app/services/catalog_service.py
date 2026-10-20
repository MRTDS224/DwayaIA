"""
Service de gestion du catalogue de médicaments officiels (CNOPS/DMP - 5 918 lignes)
Utilise RapidFuzz avec un algorithme 2-Tier :
- Tier 1 : Recherche floue directe sur les noms de marque (Ratio & Partial Ratio)
- Tier 2 : Filtrage / Boost conjoint sur le dosage (500mg, 1000mg, etc.) et la forme
"""
import openpyxl
from rapidfuzz import process, fuzz
from typing import List, Optional, Dict
from challenge1.app.config import MEDICAMENTS_FILE
from challenge1.app.core.normalizer import normalize_query

class CatalogService:
    def __init__(self):
        self.drugs: List[Dict] = []
        self.drugs_by_code: Dict[str, Dict] = {}
        self.drugs_by_dci: Dict[str, List[Dict]] = {}
        self.drug_names_lower: List[str] = []
        self._load_data()

    def _load_data(self):
        """Charge le catalogue Excel CNOPS en mémoire (5 918 médicaments)."""
        if not MEDICAMENTS_FILE.exists():
            print(f"[!] Fichier de référence non trouvé: {MEDICAMENTS_FILE}")
            return

        wb = openpyxl.load_workbook(MEDICAMENTS_FILE, read_only=True, data_only=True)
        sheet = wb.active

        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return

        headers = [str(h).strip().upper() if h is not None else "" for h in rows[0]]
        
        for r in rows[1:]:
            if not r or not r[0]:
                continue
            
            code = str(r[0]).strip()
            nom = str(r[1]).strip() if r[1] else ""
            dci = str(r[2]).strip() if r[2] else ""
            dosage = str(r[3]).strip() if r[3] else ""
            unite = str(r[4]).strip() if r[4] else ""
            forme = str(r[5]).strip() if r[5] else ""
            presentation = str(r[6]).strip() if r[6] else ""
            
            try:
                ppv = float(r[7]) if r[7] is not None else 0.0
            except:
                ppv = 0.0
            try:
                ph = float(r[8]) if r[8] is not None else 0.0
            except:
                ph = 0.0
            try:
                prix_br = float(r[9]) if r[9] is not None else 0.0
            except:
                prix_br = 0.0

            pg = str(r[10]).strip() if r[10] else "P"
            taux = str(r[11]).strip() if r[11] else "0%"

            item = {
                "code": code,
                "nom": nom,
                "dci": dci,
                "dosage": dosage,
                "unite_dosage": unite,
                "forme": forme,
                "presentation": presentation,
                "ppv": ppv,
                "ph": ph,
                "prix_br": prix_br,
                "princeps_generique": "Princeps" if pg.upper() == "P" else "Générique",
                "taux_remboursement": taux,
            }

            self.drugs.append(item)
            self.drugs_by_code[code] = item

            dci_key = normalize_query(dci)
            if dci_key:
                if dci_key not in self.drugs_by_dci:
                    self.drugs_by_dci[dci_key] = []
                self.drugs_by_dci[dci_key].append(item)

        self.drug_names_lower = [d["nom"].lower() for d in self.drugs]
        print(f"[✓] Catalogue CNOPS chargé en mémoire : {len(self.drugs)} médicaments indexés.")

    def search(self, query: str, limit: int = 5, min_score: float = 40.0) -> List[Dict]:
        """
        Recherche floue tolérante aux fautes de frappe :
        Isole les mots-clés de marque des valeurs de dosage (ex: 'doli' + '1000').
        """
        if not query or not self.drug_names_lower:
            return []

        tokens = normalize_query(query).split()
        if not tokens:
            return []

        # Séparer les chiffres (dosage) des lettres (marque/dci)
        text_tokens = [t for t in tokens if not t.isdigit() and t not in ["mg", "g", "ml"]]
        num_tokens = [t for t in tokens if t.isdigit()]

        brand_query = " ".join(text_tokens) if text_tokens else query.lower()

        # Phase 1 : Scorer par rapport au nom de médicament
        scorer = fuzz.ratio if len(brand_query) > 4 else fuzz.partial_ratio
        raw_matches = process.extract(
            brand_query,
            self.drug_names_lower,
            scorer=scorer,
            limit=limit * 5
        )

        candidates = []
        seen_codes = set()

        for match_nom, base_score, idx in raw_matches:
            if base_score < min_score:
                continue
            
            drug = self.drugs[idx].copy()
            if drug["code"] in seen_codes:
                continue

            final_score = float(base_score)

            # Boost si le dosage demandé correspond exactement au dosage du SKU
            if num_tokens:
                target_num = num_tokens[0]
                drug_dosage = str(drug.get("dosage", "")).split(".")[0].strip()
                if target_num == drug_dosage or target_num in drug["nom"]:
                    final_score += 20.0  # Fort boost dosage

            drug["similarity_score"] = round(final_score, 2)
            candidates.append(drug)
            seen_codes.add(drug["code"])

        # Trier par score composite décroissant
        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        return candidates[:limit]

    def get_by_code(self, cip_code: str) -> Optional[Dict]:
        """Récupère la fiche détaillée par code CIP."""
        return self.drugs_by_code.get(str(cip_code).strip())

    def get_alternatives(self, cip_code: str) -> List[Dict]:
        """
        Trouve les alternatives thérapeutiques et génériques partageant la même DCI.
        """
        target = self.get_by_code(cip_code)
        if not target or not target.get("dci"):
            return []

        dci_key = normalize_query(target["dci"])
        candidates = self.drugs_by_dci.get(dci_key, [])

        alternatives = [
            c for c in candidates 
            if c["code"] != target["code"]
        ]
        alternatives.sort(key=lambda x: x["ppv"])
        return alternatives

# Instance singleton partagée
catalog_service = CatalogService()
