import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from config.database import get_db
from routes.auth import auth_bp
from routes.incidents import incidents_bp
from routes.stats import stats_bp
from routes.export import export_bp
from routes.forages import forages_bp
from routes.uploads import uploads_bp

load_dotenv()

def create_app():
    app = Flask(__name__)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    from flask import send_from_directory
    @app.route("/api/uploads/<filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    app.register_blueprint(auth_bp,      url_prefix="/api/auth")
    app.register_blueprint(incidents_bp, url_prefix="/api/incidents")
    app.register_blueprint(stats_bp,     url_prefix="/api/stats")
    app.register_blueprint(export_bp,    url_prefix="/api/export")
    app.register_blueprint(forages_bp,   url_prefix="/api/forages")
    app.register_blueprint(uploads_bp,   url_prefix="/api/uploads")

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "SNDE Incidents API"}), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Route introuvable"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Methode non autorisee"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Erreur interne du serveur"}), 500

    return app


def create_admin_initial():
    import bcrypt
    db = get_db()

    # Supprimer l'ancien index email s'il existe
    try:
        db.users.drop_index("email_1")
        print("Ancien index email supprime.")
    except Exception:
        pass

    # Creer index matricule
    db.users.create_index("matricule", unique=True, sparse=True)

    if db.users.count_documents({}) == 0:
        hashed = bcrypt.hashpw("Admin1234!".encode(), bcrypt.gensalt())
        db.users.insert_one({
            "nom": "Administrateur SNDE",
            "matricule": "ADMIN001",
            "password": hashed,
            "role": "admin",
            "brigade": None,
            "actif": True
        })
        print("Compte admin cree : ADMIN001 / Admin1234!")
        print("IMPORTANT : Changez ce mot de passe!")

    db.incidents.create_index("date_declaration")
    db.incidents.create_index("statut")
    db.incidents.create_index("brigade")
    db.incidents.create_index("site")
    db.incidents.create_index("impact")
    print("Index MongoDB crees.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        create_admin_initial()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    print(f"SNDE API demarree sur http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)