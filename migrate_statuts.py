# -*- coding: utf-8 -*-
"""
Script de migration : normalise les statuts et impacts en base MongoDB.
- "Acheve" / "Abandonne" / "Debloque apres 4h" -> sans accents
- Impacts anciens -> nouveau vocabulaire (Critique/Majeure/Moyenne/Mineure)

Lancer une seule fois : python migrate_statuts.py
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/snde_db")
client = MongoClient(MONGO_URI)
db = client.get_default_database() if "/" in MONGO_URI.rsplit("/", 1)[-1] else client["snde_db"]
# Recupere le nom de la base depuis l'URI
db_name = MONGO_URI.rsplit("/", 1)[-1].split("?")[0] or "snde_db"
db = client[db_name]

col = db.incidents

# ── 1. Normalisation des STATUTS ──────────────────────────────────────────────
statuts_map = {
    "Achev\u00e9":            "Acheve",
    "Abandonn\u00e9":         "Abandonne",
    "D\u00e9bloqu\u00e9 apr\u00e8s 4h": "Debloque apres 4h",
}

total_statuts = 0
for ancien, nouveau in statuts_map.items():
    res = col.update_many({"statut": ancien}, {"$set": {"statut": nouveau}})
    if res.modified_count:
        print(f"  Statut '{ancien}' -> '{nouveau}' : {res.modified_count} incidents mis a jour")
        total_statuts += res.modified_count

# ── 2. Normalisation des IMPACTS ──────────────────────────────────────────────
impacts_map = {
    "Majeur":        "Critique",
    "Moyen":         "Moyenne",
    "Faible":        "Mineure",
    "Pas d'impact":  "Mineure",
}

total_impacts = 0
for ancien, nouveau in impacts_map.items():
    res = col.update_many({"impact": ancien}, {"$set": {"impact": nouveau}})
    if res.modified_count:
        print(f"  Impact '{ancien}' -> '{nouveau}' : {res.modified_count} incidents mis a jour")
        total_impacts += res.modified_count

print(f"\nMigration terminee : {total_statuts} statuts + {total_impacts} impacts normalises.")
print("Vous pouvez relancer le backend.")
