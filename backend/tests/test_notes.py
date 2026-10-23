import pytest
from app.models.note import Note
from app.models.user import User

@pytest.fixture
def auth_header(client):
    signup_payload = {
        "username": "jsmith_color",
        "email": "jsmith@example.com",
        "password": "Balayage2026"
    }
    client.post("/api/auth/signup", json=signup_payload)
    login_res = client.post("/api/auth/login", json={
        "email": "jsmith@example.com",
        "password": "Balayage2026"
    })
    token = login_res.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}

def test_get_notes_options(client):
    """Verify lookup options endpoint returns standard brands and developers."""
    res = client.get("/api/notes/options")
    assert res.status_code == 200
    data = res.get_json()
    assert "brands" in data
    assert "developers" in data
    assert "Redken" in data["brands"]
    assert "20 vol" in data["developers"]

def test_create_note_success(client, auth_header):
    """TC-NOTE-01: Create a formula note with valid data."""
    payload = {
        "title": "Maria R. - root touch-up",
        "brand": "Redken",
        "shades": "6NB + 7N",
        "developer": "20 vol",
        "processing_time": 35,
        "notes": "Apply roots first, pull through last 10 min",
        "is_public": False
    }
    res = client.post("/api/notes", json=payload, headers=auth_header)
    assert res.status_code == 201

    data = res.get_json()
    assert data["message"] == "Formula note created successfully"
    assert "note" in data
    note = data["note"]
    assert note["title"] == "Maria R. - root touch-up"
    assert note["brand"] == "Redken"
    assert note["shades"] == "6NB + 7N"
    assert note["developer"] == "20 vol"
    assert note["processing_time"] == 35
    assert note["notes"] == "Apply roots first, pull through last 10 min"
    assert note["is_public"] is False
    assert note["author_username"] == "jsmith_color"
    assert "id" in note

    # Verify note in database
    db_note = Note.query.filter_by(title="Maria R. - root touch-up").first()
    assert db_note is not None
    assert db_note.brand == "Redken"
    assert db_note.shades == "6NB + 7N"
    assert db_note.processing_time == 35

def test_create_note_missing_required_fields(client, auth_header):
    """TC-NOTE-01: Reject note with missing brand, shades, or title."""
    # Missing brand and shades
    res = client.post("/api/notes", json={
        "title": "Incomplete Note",
        "developer": "20 vol",
        "processing_time": 30
    }, headers=auth_header)
    assert res.status_code == 400
    data = res.get_json()
    assert "missing required fields" in data["error"].lower()
    assert "brand" in data["error"].lower()
    assert "shades" in data["error"].lower()

    # Missing title
    res2 = client.post("/api/notes", json={
        "brand": "Wella",
        "shades": "8A",
        "developer": "10 vol",
        "processing_time": 25
    }, headers=auth_header)
    assert res2.status_code == 400

def test_create_note_invalid_processing_time(client, auth_header):
    """TC-NOTE-01: Processing time must be at least 1 minute."""
    # Zero processing time
    res = client.post("/api/notes", json={
        "title": "Zero Time Note",
        "brand": "Redken",
        "shades": "5N",
        "developer": "20 vol",
        "processing_time": 0
    }, headers=auth_header)
    assert res.status_code == 400
    data = res.get_json()
    assert "at least 1 minute" in data["error"].lower()

    # Negative processing time
    res2 = client.post("/api/notes", json={
        "title": "Negative Time Note",
        "brand": "Redken",
        "shades": "5N",
        "developer": "20 vol",
        "processing_time": -5
    }, headers=auth_header)
    assert res2.status_code == 400

    # Non-integer processing time
    res3 = client.post("/api/notes", json={
        "title": "Invalid String Time",
        "brand": "Redken",
        "shades": "5N",
        "developer": "20 vol",
        "processing_time": "invalid"
    }, headers=auth_header)
    assert res3.status_code == 400

    # Boundary: processing_time = 1 is valid
    res4 = client.post("/api/notes", json={
        "title": "Boundary 1 Min Note",
        "brand": "Redken",
        "shades": "5N",
        "developer": "20 vol",
        "processing_time": 1
    }, headers=auth_header)
    assert res4.status_code == 201
    assert res4.get_json()["note"]["processing_time"] == 1

def test_create_note_unauthenticated(client):
    """Reject note creation when Authorization header is missing."""
    res = client.post("/api/notes", json={
        "title": "No Auth Note",
        "brand": "Redken",
        "shades": "6NB",
        "developer": "20 vol",
        "processing_time": 30
    })
    assert res.status_code == 401

def test_list_notes_returns_only_own_notes(client, auth_header):
    """TC-PROF-01: List notes returns only the authenticated user's notes."""
    # Create two notes for jsmith_color
    client.post("/api/notes", json={
        "title": "Note 1",
        "brand": "Redken",
        "shades": "6NB",
        "developer": "20 vol",
        "processing_time": 30
    }, headers=auth_header)

    client.post("/api/notes", json={
        "title": "Note 2",
        "brand": "Wella",
        "shades": "7A",
        "developer": "10 vol",
        "processing_time": 25
    }, headers=auth_header)

    res = client.get("/api/notes", headers=auth_header)
    assert res.status_code == 200
    notes = res.get_json()["notes"]
    assert len(notes) >= 2
    for n in notes:
        assert n["author_username"] == "jsmith_color"

def test_update_note_success(client, auth_header):
    """TC-NOTE-02: Successfully update an existing note."""
    create_res = client.post("/api/notes", json={
        "title": "Original Title",
        "brand": "Redken",
        "shades": "7N",
        "developer": "20 vol",
        "processing_time": 30
    }, headers=auth_header)
    note_id = create_res.get_json()["note"]["id"]

    update_res = client.put(f"/api/notes/{note_id}", json={
        "title": "Updated Title - Follow-up Adjustment",
        "brand": "Wella",
        "shades": "8N",
        "developer": "10 vol",
        "processing_time": 25,
        "notes": "Adjusted after follow-up",
        "is_public": True
    }, headers=auth_header)

    assert update_res.status_code == 200
    data = update_res.get_json()
    assert data["message"] == "Formula note updated successfully"
    assert data["note"]["title"] == "Updated Title - Follow-up Adjustment"
    assert data["note"]["brand"] == "Wella"
    assert data["note"]["notes"] == "Adjusted after follow-up"
    assert data["note"]["is_public"] is True