import bcrypt
from flask import Blueprint, request, jsonify
from bson import ObjectId
from config.database import get_db
from middleware.auth import generate_token, token_required, role_required

auth_bp = Blueprint("auth", __name__)

ROLES = ["employe", "chef_brigade", "directeur", "admin"]

BRIGADES = [
    "Brigade D'Aftout Echergui",
    "Brigade de Dhar",
    "Brigade du Nord",
    "Brigade de Boulenoir",
    "Brigade d'Idini",
    "Brigade du centre",
    "Brigade de dessalement",
    "Brigade du Hod Egharbi",
    "Brigade de Kiffa",
    "Département Eaux de Surface"
]


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("matricule") or not data.get("password"):
        return jsonify({"error": "Matricule et mot de passe requis"}), 400

    db = get_db()
    user = db.users.find_one({"matricule": data["matricule"].strip()})
    if not user:
        return jsonify({"error": "Matricule ou mot de passe incorrect"}), 401

    if not bcrypt.checkpw(data["password"].encode(), user["password"]):
        return jsonify({"error": "Matricule ou mot de passe incorrect"}), 401

    token = generate_token(
        user_id=user["_id"],
        email=user.get("matricule"),
        role=user["role"],
        brigade=user.get("brigade")
    )
    return jsonify({
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "nom": user["nom"],
            "matricule": user["matricule"],
            "role": user["role"],
            "brigade": user.get("brigade")
        }
    }), 200


@auth_bp.route("/register", methods=["POST"])
@role_required("admin")
def register():
    data = request.get_json()
    required = ["nom", "matricule", "password", "role"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Champ requis : {field}"}), 400

    if data["role"] not in ROLES:
        return jsonify({"error": f"Role invalide. Valeurs acceptees : {ROLES}"}), 400

    db = get_db()
    matricule = data["matricule"].strip()
    if db.users.find_one({"matricule": matricule}):
        return jsonify({"error": "Ce matricule existe deja"}), 409

    hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())
    new_user = {
        "nom": data["nom"],
        "matricule": matricule,
        "password": hashed,
        "role": data["role"],
        "brigade": data.get("brigade"),
        "actif": True
    }
    result = db.users.insert_one(new_user)
    return jsonify({
        "message": "Utilisateur cree",
        "id": str(result.inserted_id)
    }), 201


@auth_bp.route("/me", methods=["GET"])
@token_required
def me():
    db = get_db()
    user = db.users.find_one({"_id": ObjectId(request.user["id"])})
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    return jsonify({
        "id": str(user["_id"]),
        "nom": user["nom"],
        "matricule": user.get("matricule"),
        "role": user["role"],
        "brigade": user.get("brigade")
    }), 200


@auth_bp.route("/change-password", methods=["PUT"])
@token_required
def change_password():
    data = request.get_json()
    if not data.get("ancien_mdp") or not data.get("nouveau_mdp"):
        return jsonify({"error": "Champs requis : ancien_mdp, nouveau_mdp"}), 400

    db = get_db()
    user = db.users.find_one({"_id": ObjectId(request.user["id"])})
    if not bcrypt.checkpw(data["ancien_mdp"].encode(), user["password"]):
        return jsonify({"error": "Ancien mot de passe incorrect"}), 401

    hashed = bcrypt.hashpw(data["nouveau_mdp"].encode(), bcrypt.gensalt())
    db.users.update_one({"_id": user["_id"]}, {"$set": {"password": hashed}})
    return jsonify({"message": "Mot de passe mis a jour"}), 200


@auth_bp.route("/users", methods=["GET"])
@role_required("admin", "directeur")
def list_users():
    db = get_db()
    users = list(db.users.find({}, {"password": 0}))
    for u in users:
        u["_id"] = str(u["_id"])
    return jsonify(users), 200


@auth_bp.route("/users/<user_id>", methods=["PUT"])
@role_required("admin")
def update_user(user_id):
    data = request.get_json()
    updates = {}
    if data.get("role"):
        if data["role"] not in ROLES:
            return jsonify({"error": "Role invalide"}), 400
        updates["role"] = data["role"]
    if data.get("brigade") is not None:
        updates["brigade"] = data["brigade"]
    if data.get("actif") is not None:
        updates["actif"] = bool(data["actif"])

    db = get_db()
    try:
        db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    except Exception:
        return jsonify({"error": "ID invalide"}), 400
    return jsonify({"message": "Utilisateur mis a jour"}), 200


@auth_bp.route("/users/<user_id>", methods=["DELETE"])
@role_required("admin")
def delete_user(user_id):
    db = get_db()
    # On ne permet pas à un admin de se supprimer lui-même (sécurité)
    if str(request.user["id"]) == user_id:
        return jsonify({"error": "Vous ne pouvez pas supprimer votre propre compte"}), 400
        
    try:
        db.users.delete_one({"_id": ObjectId(user_id)})
    except Exception:
        return jsonify({"error": "ID invalide"}), 400
    return jsonify({"message": "Utilisateur supprime"}), 200