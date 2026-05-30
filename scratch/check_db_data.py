import sys
import os
sys.path.append(os.getcwd())

from config.database import get_db

def check_data():
    db = get_db()
    incidents = db.incidents.find().limit(100)
    statuts = db.incidents.distinct("statut")
    impacts = db.incidents.distinct("impact")
    
    print("--- Statistiques de la base de données ---")
    print(f"Nombre total d'incidents : {db.incidents.count_documents({})}")
    print(f"Valeurs uniques de 'statut' : {statuts}")
    print(f"Valeurs uniques de 'impact' : {impacts}")
    
    # Vérifier le type de la date
    sample = db.incidents.find_one()
    if sample:
        print(f"Exemple d'incident : {sample.get('site')} - {sample.get('description')}")
        print(f"Type de 'date_declaration' : {type(sample.get('date_declaration'))}")
        print(f"Valeur de 'date_declaration' : {sample.get('date_declaration')}")

if __name__ == "__main__":
    check_data()
