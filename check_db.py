from config.database import get_db
import os
from dotenv import load_dotenv

load_dotenv()

db = get_db()
count = db.forages.count_documents({})
print(f"Nombre de forages: {count}")
if count > 0:
    for f in db.forages.find().limit(3):
        print(f" - {f['nom']} ({f['site']})")
else:
    print("La collection 'forages' est vide.")
