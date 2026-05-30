import sys
import os
sys.path.append(os.getcwd())

from config.database import get_db

def migrate_data():
    db = get_db()
    print("Dbut de la migration des données...")
    
    # 1. Harmonisation des IMPACTS
    # Faible -> Mineure, Moyen -> Moyenne, Majeur -> Majeure
    impact_map = {
        "Faible": "Mineure",
        "Moyen": "Moyenne",
        "Majeur": "Majeure"
    }
    for old, new in impact_map.items():
        res = db.incidents.update_many({"impact": old}, {"$set": {"impact": new}})
        print(f"Impact: {old} -> {new} ({res.modified_count} documents modifis)")

    # 2. Harmonisation des STATUTS et Correction Encodage
    # On va utiliser des regex ou des patterns pour attraper les variations avec mauvais encodage
    
    # Achev -> Acheve (on enlve l'accent pour simplifier ou on met le bon)
    # Le frontend utilise : 'En attente', 'En cours', 'Acheve', 'Abandonne', 'Debloque apres 4h'
    # NOTE: J'ai vu que le frontend utilise 'Acheve' sans accent dans STATUTS constant
    
    status_updates = [
        ({"statut": {"$regex": "^Achev", "$options": "i"}}, "Acheve"),
        ({"statut": {"$regex": "^Abandonn", "$options": "i"}}, "Abandonne"),
        ({"statut": {"$regex": "^D.bloqu", "$options": "i"}}, "Debloque apres 4h"),
        ({"statut": "En attente"}, "En attente") # Juste pour tre sr
    ]
    
    for query, new_val in status_updates:
        res = db.incidents.update_many(query, {"$set": {"statut": new_val}})
        print(f"Statut: {query} -> {new_val} ({res.modified_count} documents modifis)")

    print("Migration terminee !")

if __name__ == "__main__":
    migrate_data()
