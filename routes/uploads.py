from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from middleware.auth import token_required
import uuid

uploads_bp = Blueprint("uploads", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@uploads_bp.route("", methods=["POST"])
@token_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier fourni"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Aucun fichier selectionne"}), 400
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{uuid.uuid4().hex}.{ext}")
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        photo_url = f"/uploads/{filename}"
        return jsonify({"message": "Fichier telecharge", "photo_url": photo_url}), 201
    return jsonify({"error": "Type de fichier non autorise"}), 400
