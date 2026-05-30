import sys
import os
sys.path.append(os.getcwd())

from config.database import get_db

def check_statuts():
    db = get_db()
    pipeline = [
        {"$group": {"_id": "$statut", "count": {"$sum": 1}}}
    ]
    results = list(db.incidents.aggregate(pipeline))
    print("--- Décompte des statuts dans la base ---")
    for r in results:
        print(f"Statut: '{r['_id']}' | Nombre: {r['count']}")

if __name__ == "__main__":
    check_statuts()
