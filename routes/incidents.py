from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime, timezone, timedelta
from config.database import get_db
from middleware.auth import token_required, role_required

incidents_bp = Blueprint("incidents", __name__)

STATUTS = ["En attente", "En cours", "Acheve", "Abandonne", "Debloque apres 4h"]
IMPACTS = ["Critique", "Majeure", "Moyenne", "Mineure"]
BRIGADES = [
    "Brigade D'Aftout Echergui", "Brigade de Dhar", "Brigade du Nord",
    "Brigade de Boulenoir", "Brigade d'Idini", "Brigade du centre",
    "Brigade de dessalement", "Brigade du Hod Egharbi",
    "Brigade de Kiffa", "Département Eaux de Surface"
]

CAUSES = [
    "Usure normale", "Mauvaise maintenance", "Surcharge", "Vieillissement",
    "Corrosion", "Erreur humaine", "Défaut fabrication", "Mauvaise installation",
    "Variation tension", "Conditions climatiques", "Qualité eau", "Vibrations",
    "Mauvais dimensionnement", "Absence lubrification", "Autre"
]

TYPES_DEFAILLANCE = [
    "Vibrations excessives", "Bruit anormal", "Désalignement moteur/pompe", "Échauffement des roulements",
    "Usure des roulements", "Fuite garniture mécanique", "Fuite d'huile", "Cavitation", "Corrosion",
    "Turbine usée", "Axe cassé", "Grippage", "Désamorçage", "Débit insuffisant", "Pression insuffisante",
    "Surpression", "Pompe bloquée", "Pompe ne démarre pas", "Fonctionnement intermittent",
    "Surcharge moteur", "Court-circuit", "Perte de phase", "Baisse tension", "Surtension",
    "Échauffement moteur", "Défaut isolement", "Déclenchement disjoncteur", "Mauvais câblage", "Variateur défaillant",
    "Prise d'air aspiration", "Colmatage aspiration", "Clapet anti-retour défectueux", "Fuite conduite aspiration",
    "Fuite conduite refoulement", "Entrée sable/boue",
    "Niveau dynamique trop bas", "Marche à sec", "Surcharge immergée", "Câble immergé détérioré",
    "Corrosion colonne", "Colonne rompue", "Pompe coincée dans forage", "Présence sable", "Débit faible",
    "Pompe noyée", "Défaillance moteur immergé", "Remontée d'eau insuffisante", "Défaut sonde niveau", "Défaut capteur pression",
    "Corrosion interne", "Corrosion externe", "Fuite bride", "Rupture colonne", "Dévissage colonne",
    "Obstruction", "Déformation", "Fissure", "Usure filetages", "Encrassement calcaire", "Coup de bélier", "Mauvaise étanchéité",
    "Fuite", "Rupture conduite", "Perforation", "Affaissement canalisation",
    "Déboîtement", "Écrasement", "Vieillissement matériau", "Perte de charge élevée",
    "Contre-pente", "Poche d'air", "Colmatage", "Envasement", "Obstruction partielle/totale",
    "Érosion terrain", "Exposition conduite", "Inondation", "Glissement terrain", "Dommage travaux tiers",
    "Vanne bloquée", "Vanne cassée", "Fuite vanne", "Vanne grippée", "Mauvaise fermeture", "Commande défectueuse",
    "Joint détérioré", "Desserrage boulons", "Corrosion raccord", "Mauvais alignement",
    "Inondation regard", "Couvercle endommagé", "Accumulation boue", "Accès obstrué", "Manomètre défectueux",
    "Débitmètre hors service", "Compteur hors service", "Compteur bloqué", "Capteur pression défaillant",
    "Sonde niveau défectueuse", "Transmission SCADA perdue",
    "Coupure électrique", "Chute tension", "Surtension", "Déséquilibre phases", "Perte phase", "Fréquence instable",
    "Câble coupé", "Câble brûlé", "Mauvais serrage", "Défaut isolement", "Échauffement câble",
    "Fusible grillé", "Relais défectueux", "Protection thermique HS", "Défaut mise à terre",
    "Surchauffe transformateur", "Fuite huile transformateur", "Groupe électrogène ne démarre pas", "Batterie faible", "Défaut alternateur",
    "Contacteur défectueux", "Relais HS", "Automate en défaut", "Variateur en panne", "Carte électronique HS",
    "Alimentation commande HS", "Surchauffe armoire", "Ventilation insuffisante", "Ventilateur HS", "Climatisation armoire HS",
    "Perte communication", "Défaut automate PLC", "Défaut télémétrie", "Défaut capteurs", "Alarme non fonctionnelle",
    "Corrosion armoire", "Infiltration eau", "Présence poussière", "Porte endommagée", "Serrure cassée", "Autre"
]


def incident_to_dict(inc):
    inc["_id"] = str(inc["_id"])
    if isinstance(inc.get("date_declaration"), datetime):
        inc["date_declaration"] = inc["date_declaration"].isoformat()
    if isinstance(inc.get("date_cloture"), datetime):
        inc["date_cloture"] = inc["date_cloture"].isoformat()
    if isinstance(inc.get("created_at"), datetime):
        inc["created_at"] = inc["created_at"].isoformat()
    if isinstance(inc.get("updated_at"), datetime):
        inc["updated_at"] = inc["updated_at"].isoformat()
    return inc


@incidents_bp.route("", methods=["POST"])
@token_required
def create_incident():
    data = request.get_json()
    required = ["site", "description", "brigade"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Champ obligatoire manquant : {field}"}), 400

    db = get_db()
    now = datetime.now(timezone.utc)

    incident = {
        "date_declaration": datetime.fromisoformat(data["date_declaration"]) if data.get("date_declaration") else now,
        "site": data["site"].strip(),
        "localisation": data.get("localisation", "").strip(),
        "description": data["description"].strip(),
        "impact": data.get("impact", "Mineure"),
        "type_defaillance": data.get("type_defaillance", "Autre"),
        "plan_action_signe": data.get("plan_action_signe", False),
        "statut": "En attente",
        "action_corrective": "",
        "brigade": data["brigade"],
        "chef_brigade": data.get("chef_brigade", ""),
        "pieces_rechange": data.get("pieces_rechange", ""),
        "date_cloture": None,
        "code_gmao": data.get("code_gmao", ""),
        "observation": data.get("observation", ""),
        "cause_probable": data.get("cause_probable", ""),
        "photo_url": data.get("photo_url", ""),
        "declare_par": request.user.get("id"),
        "declare_par_nom": request.user.get("email"),
        "created_at": now,
        "updated_at": now
    }

    result = db.incidents.insert_one(incident)
    return jsonify({"message": "Incident créé", "id": str(result.inserted_id)}), 201


@incidents_bp.route("", methods=["GET"])
@token_required
def list_incidents():
    db = get_db()
    user = request.user
    query = {}

    if user["role"] == "employe":
        query["declare_par"] = user["id"]
    elif user["role"] == "chef_brigade":
        query["brigade"] = user.get("brigade", "")

    if request.args.get("statut"):
        query["statut"] = request.args["statut"]
    if request.args.get("site"):
        query["site"] = {"$regex": request.args["site"], "$options": "i"}
    if request.args.get("brigade") and user["role"] in ["directeur", "admin"]:
        query["brigade"] = request.args["brigade"]
    if request.args.get("impact"):
        query["impact"] = request.args["impact"]
    if request.args.get("type_defaillance"):
        query["type_defaillance"] = request.args["type_defaillance"]
    if request.args.get("search"):
        query["$or"] = [
            {"description": {"$regex": request.args["search"], "$options": "i"}},
            {"site": {"$regex": request.args["search"], "$options": "i"}},
            {"localisation": {"$regex": request.args["search"], "$options": "i"}}
        ]

    if request.args.get("date_debut") or request.args.get("date_fin"):
        date_filter = {}
        if request.args.get("date_debut"):
            date_filter["$gte"] = datetime.fromisoformat(request.args["date_debut"])
        if request.args.get("date_fin"):
            date_filter["$lte"] = datetime.fromisoformat(request.args["date_fin"])
        query["date_declaration"] = date_filter

    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))
    skip = (page - 1) * limit

    total = db.incidents.count_documents(query)
    incidents = list(
        db.incidents.find(query)
        .sort("date_declaration", -1)
        .skip(skip)
        .limit(limit)
    )

    return jsonify({
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "data": [incident_to_dict(inc) for inc in incidents]
    }), 200


@incidents_bp.route("/<incident_id>", methods=["GET"])
@token_required
def get_incident(incident_id):
    db = get_db()
    try:
        inc = db.incidents.find_one({"_id": ObjectId(incident_id)})
    except Exception:
        return jsonify({"error": "ID invalide"}), 400
    if not inc:
        return jsonify({"error": "Incident introuvable"}), 404
    return jsonify(incident_to_dict(inc)), 200


@incidents_bp.route("/<incident_id>", methods=["PUT"])
@token_required
def update_incident(incident_id):
    data = request.get_json()
    db = get_db()
    user = request.user

    try:
        inc = db.incidents.find_one({"_id": ObjectId(incident_id)})
    except Exception:
        return jsonify({"error": "ID invalide"}), 400
    if not inc:
        return jsonify({"error": "Incident introuvable"}), 404

    if user["role"] == "employe" and inc.get("declare_par") != user["id"]:
        return jsonify({"error": "Accès refusé"}), 403
    if user["role"] == "chef_brigade" and inc.get("brigade") != user.get("brigade"):
        return jsonify({"error": "Accès refusé — incident hors de votre brigade"}), 403

    updates = {"updated_at": datetime.now(timezone.utc)}
    modifiable = [
        "statut", "action_corrective", "pieces_rechange",
        "chef_brigade", "code_gmao", "observation", "cause_probable",
        "impact", "localisation", "photo_url",
        "type_defaillance", "plan_action_signe"
    ]
    for field in modifiable:
        if field in data:
            updates[field] = data[field]

    if data.get("statut") == "Acheve" and not inc.get("date_cloture"):
        updates["date_cloture"] = datetime.now(timezone.utc)

    if data.get("date_cloture"):
        updates["date_cloture"] = datetime.fromisoformat(data["date_cloture"])

    db.incidents.update_one({"_id": ObjectId(incident_id)}, {"$set": updates})
    return jsonify({"message": "Incident mis à jour"}), 200


@incidents_bp.route("/<incident_id>", methods=["DELETE"])
@role_required("admin")
def delete_incident(incident_id):
    db = get_db()
    try:
        result = db.incidents.delete_one({"_id": ObjectId(incident_id)})
    except Exception:
        return jsonify({"error": "ID invalide"}), 400
    if result.deleted_count == 0:
        return jsonify({"error": "Incident introuvable"}), 404
    return jsonify({"message": "Incident supprimé"}), 200


@incidents_bp.route("/referentiels/sites", methods=["GET"])
@token_required
def get_sites():
    db = get_db()
    sites = db.incidents.distinct("site")
    sites = sorted([s for s in sites if s])
    return jsonify(sites), 200


@incidents_bp.route("/referentiels/brigades", methods=["GET"])
@token_required
def get_brigades():
    return jsonify(BRIGADES), 200


@incidents_bp.route("/referentiels/types", methods=["GET"])
@token_required
def get_types_defaillance():
    return jsonify(TYPES_DEFAILLANCE), 200


@incidents_bp.route("/par-type", methods=["GET"])
@token_required
def incidents_par_type():
    db = get_db()
    user = request.user
    match = {}
    if user["role"] == "chef_brigade":
        match["brigade"] = user.get("brigade", "")

    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": "$type_defaillance",
            "count": {"$sum": 1},
            "acheves": {"$sum": {"$cond": [{"$eq": ["$statut", "Achevé"]}, 1, 0]}},
            "en_attente": {"$sum": {"$cond": [{"$eq": ["$statut", "En attente"]}, 1, 0]}}
        }},
        {"$sort": {"count": -1}}
    ]
    result = list(db.incidents.aggregate(pipeline))
    return jsonify(result), 200


@incidents_bp.route("/duree-resolution", methods=["GET"])
@token_required
def duree_resolution():
    db = get_db()
    user = request.user
    match = {
        "statut": "Achevé",
        "date_cloture": {"$ne": None},
        "date_declaration": {"$ne": None}
    }
    if user["role"] == "chef_brigade":
        match["brigade"] = user.get("brigade", "")

    incidents = list(db.incidents.find(match, {
        "brigade": 1, "date_declaration": 1, "date_cloture": 1
    }))

    brigades = {}
    for inc in incidents:
        brigade = inc.get("brigade", "Inconnue")
        d1 = inc.get("date_declaration")
        d2 = inc.get("date_cloture")
        if d1 and d2:
            duree = (d2 - d1).total_seconds() / 3600
            if duree > 0:
                if brigade not in brigades:
                    brigades[brigade] = []
                brigades[brigade].append(duree)

    result = []
    for brigade, durees in brigades.items():
        result.append({
            "brigade": brigade,
            "duree_moyenne_heures": round(sum(durees) / len(durees), 1),
            "nb_incidents": len(durees),
            "duree_max_heures": round(max(durees), 1)
        })
    result.sort(key=lambda x: x["duree_moyenne_heures"], reverse=True)
    return jsonify(result), 200


@incidents_bp.route("/sans-plan-action", methods=["GET"])
@token_required
def incidents_sans_plan_action():
    db = get_db()
    seuil = datetime.now(timezone.utc) - timedelta(hours=48)
    query = {
        "impact": {"$in": ["Critique", "Majeure"]},
        "statut": "En attente",
        "plan_action_signe": {"$ne": True},
        "date_declaration": {"$lt": seuil}
    }
    user = request.user
    if user["role"] == "chef_brigade":
        query["brigade"] = user.get("brigade", "")

    incidents = list(db.incidents.find(query).sort("date_declaration", 1).limit(50))
    for inc in incidents:
        inc["_id"] = str(inc["_id"])
        if isinstance(inc.get("date_declaration"), datetime):
            inc["date_declaration"] = inc["date_declaration"].isoformat()
    return jsonify({"count": len(incidents), "data": incidents}), 200


@incidents_bp.route("/pieces-statistiques", methods=["GET"])
@token_required
def pieces_statistiques():
    db = get_db()
    user = request.user
    match = {"pieces_rechange": {"$ne": "", "$exists": True}}
    if user["role"] == "chef_brigade":
        match["brigade"] = user.get("brigade", "")

    incidents = list(db.incidents.find(match, {"pieces_rechange": 1, "brigade": 1}))

    pieces_count = {}
    for inc in incidents:
        pieces = inc.get("pieces_rechange", "")
        if pieces:
            for mot in pieces.split(","):
                mot = mot.strip().lower()
                if len(mot) > 3:
                    pieces_count[mot] = pieces_count.get(mot, 0) + 1

    result = [{"piece": k, "count": v} for k, v in pieces_count.items()]
    result.sort(key=lambda x: x["count"], reverse=True)
    return jsonify(result[:20]), 200