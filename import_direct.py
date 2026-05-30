import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient("mongodb://localhost:27017/")
db = client["snde_incidents"]

FICHIER = r"C:\Users\hp\Downloads\Suivi des Incidents DP 2026 FF 06.05.2026.xlsm"

df = pd.read_excel(FICHIER, sheet_name="Suivi des incidents", header=1)
print(f"Colonnes trouvées : {len(df.columns)}")
print(f"Nombre de lignes : {len(df)}")

col_map = {
    "date_declaration": "Date de declaration d'anomalie",
    "site": "Site",
    "localisation": "Localisation",
    "description": "Description de la défaillance \n(symptomes et pré diagnostique)",
    "impact": "Impacte sur la production",
    "statut": "Statut de l'intervention",
    "action_corrective": "Action Corrective",
    "brigade": "Brigade",
    "chef_brigade": "Le chef de brigade en charge",
    "pieces_rechange": "Piéces de rechange et consomable utilisée (Mentionnez le marque)",
    "date_cloture": "Date de cloture d'intervention",
    "code_gmao": "Code GMAO",
    "observation": "Observation"
}

now = datetime.now(timezone.utc)
inseres = 0
erreurs = []

for idx, row in df.iterrows():
    try:
        site = str(row.get(col_map["site"], "")).strip()
        desc = str(row.get(col_map["description"], "")).strip()
        if not site or not desc or site == "nan" or desc == "nan":
            continue

        statut_raw = str(row.get(col_map["statut"], "En attente")).strip()
        statut = statut_raw if statut_raw in [
            "Achevé", "En attente", "Abandonné", "Débloqué après 4h"
        ] else "En attente"

        impact_raw = str(row.get(col_map["impact"], "Faible")).strip()
        impact = impact_raw if impact_raw in [
            "Faible", "Moyen", "Majeur", "Pas d'impact"
        ] else "Faible"

        def parse_date(val):
            try:
                if pd.isna(val):
                    return None
            except:
                pass
            if isinstance(val, datetime):
                return val.replace(tzinfo=timezone.utc)
            try:
                return pd.to_datetime(val).to_pydatetime().replace(tzinfo=timezone.utc)
            except:
                return None

        incident = {
            "date_declaration": parse_date(row.get(col_map["date_declaration"])) or now,
            "site": site,
            "localisation": str(row.get(col_map["localisation"], "")).strip(),
            "description": desc,
            "impact": impact,
            "statut": statut,
            "action_corrective": str(row.get(col_map["action_corrective"], "")).strip(),
            "brigade": str(row.get(col_map["brigade"], "")).strip(),
            "chef_brigade": str(row.get(col_map["chef_brigade"], "")).strip(),
            "pieces_rechange": str(row.get(col_map["pieces_rechange"], "")).strip(),
            "date_cloture": parse_date(row.get(col_map["date_cloture"])),
            "code_gmao": str(row.get(col_map["code_gmao"], "")).strip(),
            "observation": str(row.get(col_map["observation"], "")).strip(),
            "photo_url": "",
            "source": "import_excel",
            "created_at": now,
            "updated_at": now
        }

        for k, v in incident.items():
            if isinstance(v, str) and v.lower() in ("nan", "none", ""):
                incident[k] = ""

        db.incidents.insert_one(incident)
        inseres += 1

    except Exception as e:
        erreurs.append(f"Ligne {idx+2} : {str(e)}")

print(f"\n✅ {inseres} incidents importés avec succès !")
if erreurs:
    print(f"⚠️ {len(erreurs)} erreurs :")
    for e in erreurs[:10]:
        print(" -", e)