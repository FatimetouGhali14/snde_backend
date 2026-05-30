from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from config.database import get_db
from middleware.auth import role_required, token_required

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/dashboard", methods=["GET"])
@role_required("directeur", "admin", "chef_brigade")
def dashboard():
    """
    GET /api/stats/dashboard
    KPIs globaux pour le tableau de bord directeur.
    Paramètres optionnels : brigade, site, annee, mois
    """
    db = get_db()
    user = request.user

    # Filtre de base selon le rôle
    match = {}
    if user["role"] == "chef_brigade":
        match["brigade"] = user.get("brigade", "")

    # Filtres optionnels
    if request.args.get("brigade") and user["role"] in ["directeur", "admin"]:
        match["brigade"] = request.args["brigade"]
    if request.args.get("site"):
        match["site"] = request.args["site"]
    if request.args.get("annee"):
        annee = int(request.args["annee"])
        match["date_declaration"] = {
            "$gte": datetime(annee, 1, 1, tzinfo=timezone.utc),
            "$lt": datetime(annee + 1, 1, 1, tzinfo=timezone.utc)
        }

    # 1. Total par statut
    pipeline_statut = [
        {"$match": match},
        {"$group": {"_id": "$statut", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    par_statut = {r["_id"]: r["count"] for r in db.incidents.aggregate(pipeline_statut)}

    # 2. Total par brigade
    pipeline_brigade = [
        {"$match": match},
        {"$group": {"_id": "$brigade", "count": {"$sum": 1}, "en_attente": {
            "$sum": {"$cond": [{"$eq": ["$statut", "En attente"]}, 1, 0]}
        }}},
        {"$sort": {"count": -1}}
    ]
    par_brigade = [
        {"brigade": r["_id"], "total": r["count"], "en_attente": r["en_attente"]}
        for r in db.incidents.aggregate(pipeline_brigade)
    ]

    # 3. Total par site (top 15)
    pipeline_site = [
        {"$match": match},
        {"$group": {"_id": "$site", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 15}
    ]
    par_site = [{"site": r["_id"], "count": r["count"]}
                for r in db.incidents.aggregate(pipeline_site)]

    # 4. Évolution mensuelle (12 derniers mois)
    il_y_a_12_mois = datetime.now(timezone.utc) - timedelta(days=365)
    pipeline_mensuel = [
        {"$match": {**match, "date_declaration": {"$gte": il_y_a_12_mois}}},
        {"$group": {
            "_id": {
                "annee": {"$year": "$date_declaration"},
                "mois": {"$month": "$date_declaration"}
            },
            "total": {"$sum": 1},
            "acheves": {"$sum": {"$cond": [{"$in": ["$statut", ["Acheve", "Achevé", "Debloque apres 4h", "Débloqué après 4h"]]}, 1, 0]}}
        }},
        {"$sort": {"_id.annee": 1, "_id.mois": 1}}
    ]
    mensuel = [
        {
            "mois": f"{r['_id']['annee']}-{r['_id']['mois']:02d}",
            "total": r["total"],
            "acheves": r["acheves"]
        }
        for r in db.incidents.aggregate(pipeline_mensuel)
    ]

    # 5. Incidents par impact
    pipeline_impact = [
        {"$match": match},
        {"$group": {"_id": "$impact", "count": {"$sum": 1}}}
    ]
    par_impact = {r["_id"]: r["count"] for r in db.incidents.aggregate(pipeline_impact)}

    # 6. Incidents majeurs en attente depuis plus de 24h (alertes)
    seuil_alerte = datetime.now(timezone.utc) - timedelta(hours=24)
    alertes = list(db.incidents.find({
        **match,
        "statut": "En attente",
        "impact": {"$in": ["Critique", "Majeure"]},
        "date_declaration": {"$lt": seuil_alerte}
    }, {"site": 1, "brigade": 1, "description": 1, "date_declaration": 1}).limit(20))
    for a in alertes:
        a["_id"] = str(a["_id"])
        if isinstance(a.get("date_declaration"), datetime):
            a["date_declaration"] = a["date_declaration"].isoformat()

    # 7. Totaux généraux
    total = db.incidents.count_documents(match)
    en_attente = par_statut.get("En attente", 0)
    # Comptabilise les deux orthographes (ancienne et nouvelle) pour les incidents resolus
    acheves = (
        par_statut.get("Acheve", 0) + par_statut.get("Achevé", 0)
        + par_statut.get("Debloque apres 4h", 0) + par_statut.get("Débloqué après 4h", 0)
    )
    majeurs = par_impact.get("Majeure", 0) + par_impact.get("Critique", 0)

    return jsonify({
        "totaux": {
            "total": total,
            "en_attente": en_attente,
            "acheves": acheves,
            "majeurs": majeurs,
            "taux_resolution": round((acheves / total * 100), 1) if total else 0
        },
        "par_statut": par_statut,
        "par_brigade": par_brigade,
        "par_site": par_site,
        "par_impact": par_impact,
        "evolution_mensuelle": mensuel,
        "alertes_critiques": alertes,
        "nb_alertes": len(alertes)
    }), 200


@stats_bp.route("/en-attente-critique", methods=["GET"])
@token_required
def incidents_critiques():
    """
    GET /api/stats/en-attente-critique
    Liste les incidents Majeur en attente depuis plus de 24h.
    """
    db = get_db()
    user = request.user
    seuil = datetime.now(timezone.utc) - timedelta(hours=24)
    query = {
        "statut": "En attente",
        "impact": {"$in": ["Critique", "Majeure"]},
        "date_declaration": {"$lt": seuil}
    }
    if user["role"] == "chef_brigade":
        query["brigade"] = user.get("brigade", "")

    incidents = list(db.incidents.find(query).sort("date_declaration", 1).limit(50))
    for inc in incidents:
        inc["_id"] = str(inc["_id"])
        if isinstance(inc.get("date_declaration"), datetime):
            inc["date_declaration"] = inc["date_declaration"].isoformat()

    return jsonify({"count": len(incidents), "data": incidents}), 200
