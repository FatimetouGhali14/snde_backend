content = '''from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime, timezone
from config.database import get_db
from middleware.auth import token_required, role_required

forages_bp = Blueprint("forages", __name__)

STATUTS_FORAGE = [
    "En service", "En panne", "Sous garantie",
    "En rebobinage", "En attente de pieces", "Hors service"
]

FORAGES_SNDE = [
    {"nom": "Forage Barkeol", "site": "Aftout Echergui", "brigade": "Brigade D'Aftout Echergui", "lat": 17.88, "lng": -12.52},
    {"nom": "Forage Kankossa", "site": "Aftout Echergui", "brigade": "Brigade D'Aftout Echergui", "lat": 15.94, "lng": -11.44},
    {"nom": "Forage Dhar", "site": "Dhar", "brigade": "Brigade de Dhar", "lat": 16.52, "lng": -13.16},
    {"nom": "Forage Boughla", "site": "Dhar", "brigade": "Brigade de Dhar", "lat": 16.68, "lng": -13.22},
    {"nom": "Forage Atar", "site": "Adrar", "brigade": "Brigade du Nord", "lat": 20.52, "lng": -13.05},
    {"nom": "Forage Chinguetti", "site": "Adrar", "brigade": "Brigade du Nord", "lat": 20.45, "lng": -12.37},
    {"nom": "Forage Boulenoir", "site": "Boulenoir", "brigade": "Brigade de Boulenoir", "lat": 18.08, "lng": -15.75},
    {"nom": "Forage Idini F1", "site": "Idini", "brigade": "Brigade d'Idini", "lat": 18.10, "lng": -15.92},
    {"nom": "Forage Idini F2", "site": "Idini", "brigade": "Brigade d'Idini", "lat": 18.12, "lng": -15.90},
    {"nom": "Forage Idini F3", "site": "Idini", "brigade": "Brigade d'Idini", "lat": 18.09, "lng": -15.93},
    {"nom": "Forage Chami", "site": "Chami", "brigade": "Brigade du centre", "lat": 19.92, "lng": -15.03},
    {"nom": "Forage Aioun", "site": "Aioun", "brigade": "Brigade du Hod Egharbi", "lat": 16.66, "lng": -9.61},
    {"nom": "Forage Tintane", "site": "Tintane", "brigade": "Brigade du Hod Egharbi", "lat": 16.06, "lng": -8.97},
    {"nom": "Forage Kiffa", "site": "Kiffa", "brigade": "Brigade de Kiffa", "lat": 16.62, "lng": -11.40},
    {"nom": "Forage Rosso", "site": "Rosso", "brigade": "Departement Eaux de Surface", "lat": 16.51, "lng": -15.81},
    {"nom": "Station Dessalement 1", "site": "Dessalement", "brigade": "Brigade de dessalement", "lat": 20.93, "lng": -17.03},
    {"nom": "Forage Bassiknou", "site": "Bassiknou", "brigade": "Brigade du Hod Egharbi", "lat": 15.78, "lng": -5.99},
    {"nom": "Forage Oualata", "site": "Oualata", "brigade": "Brigade du Hod Egharbi", "lat": 17.29, "lng": -7.02},
    {"nom": "Forage Tidjikja", "site": "Tidjikja", "brigade": "Brigade du centre", "lat": 18.56, "lng": -11.42},
    {"nom": "Forage Tekane", "site": "Tekane", "brigade": "Departement Eaux de Surface", "lat": 16.62, "lng": -15.17},
]


@forages_bp.route("", methods=["GET"])
@token_required
def list_forages():
    db = get_db()
    user = request.user
    forages = list(db.forages.find({}))
    if not forages:
        now = datetime.now(timezone.utc)
        for f in FORAGES_SNDE:
            db.forages.insert_one({**f, "statut": "En service", "created_at": now, "updated_at": now})
        forages = list(db.forages.find({}))
    if user["role"] == "chef_brigade":
        brigade = user.get("brigade", "")
        forages = [f for f in forages if f.get("brigade") == brigade]
    result = []
    for f in forages:
        f_id = str(f["_id"])
        total = db.incidents.count_documents({"site": f["site"]})
        en_attente = db.incidents.count_documents({"site": f["site"], "statut": "En attente"})
        f["_id"] = f_id
        f["total_incidents"] = total
        f["incidents_en_attente"] = en_attente
        result.append(f)
    return jsonify(result), 200


@forages_bp.route("/carte", methods=["GET"])
@token_required
def carte_forages():
    db = get_db()
    pipeline = [
        {"$group": {
            "_id": "$site",
            "total": {"$sum": 1},
            "en_attente": {"$sum": {"$cond": [{"$eq": ["$statut", "En attente"]}, 1, 0]}},
            "majeurs": {"$sum": {"$cond": [{"$eq": ["$impact", "Majeur"]}, 1, 0]}}
        }}
    ]
    stats_par_site = {r["_id"]: r for r in db.incidents.aggregate(pipeline)}
    result = []
    sites_vus = set()
    for f in FORAGES_SNDE:
        site = f["site"]
        if site not in sites_vus:
            sites_vus.add(site)
            stats = stats_par_site.get(site, {"total": 0, "en_attente": 0, "majeurs": 0})
            if stats["majeurs"] > 0 and stats["en_attente"] > 0:
                couleur = "rouge"
            elif stats["en_attente"] > 0:
                couleur = "orange"
            else:
                couleur = "vert"
            result.append({
                "site": site,
                "brigade": f["brigade"],
                "lat": f["lat"],
                "lng": f["lng"],
                "total_incidents": stats["total"],
                "en_attente": stats["en_attente"],
                "majeurs": stats["majeurs"],
                "couleur": couleur
            })
    return jsonify(result), 200


@forages_bp.route("/<forage_id>", methods=["GET"])
@token_required
def get_forage(forage_id):
    db = get_db()
    try:
        forage = db.forages.find_one({"_id": ObjectId(forage_id)})
    except Exception:
        return jsonify({"error": "ID invalide"}), 400
    if not forage:
        return jsonify({"error": "Forage introuvable"}), 404
    incidents = list(db.incidents.find(
        {"site": forage["site"]},
        {"description": 1, "statut": 1, "impact": 1, "date_declaration": 1, "date_cloture": 1, "type_defaillance": 1}
    ).sort("date_declaration", -1).limit(20))
    for inc in incidents:
        inc["_id"] = str(inc["_id"])
        if isinstance(inc.get("date_declaration"), datetime):
            inc["date_declaration"] = inc["date_declaration"].isoformat()
        if isinstance(inc.get("date_cloture"), datetime):
            inc["date_cloture"] = inc["date_cloture"].isoformat()
    forage["_id"] = str(forage["_id"])
    forage["historique"] = incidents
    return jsonify(forage), 200


@forages_bp.route("/<forage_id>", methods=["PUT"])
@role_required("admin", "chef_brigade", "directeur")
def update_forage(forage_id):
    data = request.get_json()
    db = get_db()
    updates = {"updated_at": datetime.now(timezone.utc)}
    if data.get("statut"):
        if data["statut"] not in STATUTS_FORAGE:
            return jsonify({"error": "Statut invalide"}), 400
        updates["statut"] = data["statut"]
    if data.get("observation"):
        updates["observation"] = data["observation"]
    try:
        db.forages.update_one({"_id": ObjectId(forage_id)}, {"$set": updates})
    except Exception:
        return jsonify({"error": "ID invalide"}), 400
    return jsonify({"message": "Forage mis a jour"}), 200


@forages_bp.route("/referentiels/statuts", methods=["GET"])
@token_required
def get_statuts_forage():
    return jsonify(STATUTS_FORAGE), 200
'''

with open('routes/forages.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fichier routes/forages.py créé avec succès !")