from flask import Blueprint, jsonify, request

from ..auth.routes import token_required
from ..extensions import db
from ..models.note import Note

notes = Blueprint("notes", __name__)

STANDARD_BRANDS = [
    "Redken",
    "Wella",
    "Schwarzkopf",
    "L'Oreal",
    "Goldwell",
    "Matrix",
    "Pulp Riot",
    "Joico",
    "Kenra",
    "Other"
]

STANDARD_DEVELOPERS = [
    "5 vol",
    "10 vol",
    "20 vol",
    "30 vol",
    "40 vol"
]

@notes.get("/options")
def get_options():
    return jsonify({
        "brands": STANDARD_BRANDS,
        "developers": STANDARD_DEVELOPERS
    }), 200

@notes.post("")
@notes.post("/")
@token_required
def create_note(current_user):
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Request body must be valid JSON"}), 400

    title = data.get("title")
    brand = data.get("brand")
    shades = data.get("shades")
    developer = data.get("developer")
    processing_time = data.get("processing_time")
    note_body = data.get("notes", "")
    is_public = bool(data.get("is_public", False))

    # Required field validations
    missing = []
    if not title or not str(title).strip():
        missing.append("title")
    if not brand or not str(brand).strip():
        missing.append("brand")
    if not shades or not str(shades).strip():
        missing.append("shades")
    if not developer or not str(developer).strip():
        missing.append("developer")

    if missing:
        return jsonify({
            "error": f"Missing required fields: {', '.join(missing)}"
        }), 400

    # Processing time validation
    if processing_time is None:
        return jsonify({"error": "Processing time is required"}), 400

    try:
        proc_time_int = int(processing_time)
    except (ValueError, TypeError):
        return jsonify({"error": "Processing time must be a valid number of minutes"}), 400

    if proc_time_int < 1:
        return jsonify({"error": "Processing time must be at least 1 minute"}), 400

    new_note = Note(
        user_id=current_user.id,
        title=str(title).strip(),
        brand=str(brand).strip(),
        shades=str(shades).strip(),
        developer=str(developer).strip(),
        processing_time=proc_time_int,
        notes=str(note_body).strip() if note_body else "",
        is_public=is_public
    )

    try:
        db.session.add(new_note)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An error occurred while saving the formula note"}), 500

    return jsonify({
        "message": "Formula note created successfully",
        "note": new_note.to_dict()
    }), 201

@notes.get("")
@notes.get("/")
@token_required
def list_notes(current_user):
    user_notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
    return jsonify({
        "notes": [n.to_dict() for n in user_notes]
    }), 200
