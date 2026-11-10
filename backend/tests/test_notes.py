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

def make_auth_header(client, username):
    client.post("/api/auth/signup", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "Balayage2026"
    })
    login_res = client.post("/api/auth/login", json={
        "email": f"{username}@example.com",
        "password": "Balayage2026"
    })
    token = login_res.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}

def create_note(client, headers, **overrides):
    payload = {
        "title": "Maria R. - root touch-up",
        "brand": "Redken",
        "shades": "6NB",
        "developer": "20 vol",
        "processing_time": 30,
        "notes": "Apply roots first"
    }
    payload.update(overrides)
    res = client.post("/api/notes", json=payload, headers=headers)
    assert res.status_code == 201
    return res.get_json()["note"]

def test_partial_patch_preserves_notes(client, auth_header):
    """TC-NOTE-03: PATCH without a notes field keeps the existing notes."""
    note = create_note(client, auth_header)

    res = client.patch(f"/api/notes/{note['id']}", json={"title": "Renamed"}, headers=auth_header)
    assert res.status_code == 200
    data = res.get_json()["note"]
    assert data["title"] == "Renamed"
    assert data["notes"] == "Apply roots first"

def test_update_note_other_user_forbidden(client, auth_header):
    """TC-NOTE-04: Another user cannot edit a note; the note is unchanged."""
    note = create_note(client, auth_header)
    other_header = make_auth_header(client, "other_stylist")

    res_put = client.put(f"/api/notes/{note['id']}", json={"title": "Hijacked"}, headers=other_header)
    assert res_put.status_code == 403

    res_patch = client.patch(f"/api/notes/{note['id']}", json={"notes": "Hijacked"}, headers=other_header)
    assert res_patch.status_code == 403

    owner_notes = client.get("/api/notes", headers=auth_header).get_json()["notes"]
    assert owner_notes[0]["title"] == "Maria R. - root touch-up"
    assert owner_notes[0]["notes"] == "Apply roots first"

def test_delete_note_success(client, auth_header):
    """TC-NOTE-05: Owner can delete their note."""
    note = create_note(client, auth_header)

    res = client.delete(f"/api/notes/{note['id']}", headers=auth_header)
    assert res.status_code == 200
    assert res.get_json()["message"] == "Formula note deleted successfully"
    assert client.get("/api/notes", headers=auth_header).get_json()["notes"] == []

def test_delete_note_other_user_forbidden(client, auth_header):
    """TC-NOTE-05: Another user cannot delete a note; the note survives."""
    note = create_note(client, auth_header)
    other_header = make_auth_header(client, "other_stylist")

    res = client.delete(f"/api/notes/{note['id']}", headers=other_header)
    assert res.status_code == 403

    owner_notes = client.get("/api/notes", headers=auth_header).get_json()["notes"]
    assert [n["id"] for n in owner_notes] == [note["id"]]

def test_edit_or_delete_missing_note_returns_404(client, auth_header):
    """Editing or deleting a note that does not exist returns 404."""
    assert client.put("/api/notes/99999", json={"title": "x"}, headers=auth_header).status_code == 404
    assert client.delete("/api/notes/99999", headers=auth_header).status_code == 404

def test_search_excludes_other_users_notes(client, auth_header):
    """TC-SRCH-01: Search only returns the authenticated user's notes."""
    create_note(client, auth_header, title="Balayage - Maria")
    other_header = make_auth_header(client, "other_stylist")
    create_note(client, other_header, title="Balayage - Secret client")

    for query in ["?q=Balayage", "?q=Secret", "?q=%25", "?brand=Redken"]:
        notes = client.get(f"/api/notes{query}", headers=auth_header).get_json()["notes"]
        for n in notes:
            assert n["author_username"] == "jsmith_color"

    notes = client.get("/api/notes?q=Balayage", headers=auth_header).get_json()["notes"]
    assert [n["title"] for n in notes] == ["Balayage - Maria"]

def test_search_brand_filter(client, auth_header):
    """TC-SRCH-02: Brand filter returns only matching notes; 'All' returns everything."""
    create_note(client, auth_header, title="Redken note", brand="Redken")
    create_note(client, auth_header, title="Wella note", brand="Wella")

    notes = client.get("/api/notes?brand=Wella", headers=auth_header).get_json()["notes"]
    assert [n["title"] for n in notes] == ["Wella note"]

    notes = client.get("/api/notes?brand=All", headers=auth_header).get_json()["notes"]
    assert len(notes) == 2


def test_share_note_toggle_success(client, auth_header):
    """US-8: Owner can toggle a note from private to public and back."""
    note = create_note(client, auth_header, title="Shareable Formula", is_public=False)
    assert note["is_public"] is False

    # Share publicly
    res = client.patch(f"/api/notes/{note['id']}/share", json={"is_public": True}, headers=auth_header)
    assert res.status_code == 200
    data = res.get_json()
    assert data["message"] == "Note share status updated"
    assert data["note"]["is_public"] is True

    # Unshare (make private again)
    res2 = client.patch(f"/api/notes/{note['id']}/share", json={"is_public": False}, headers=auth_header)
    assert res2.status_code == 200
    assert res2.get_json()["note"]["is_public"] is False


def test_share_note_other_user_forbidden(client, auth_header):
    """US-8: Another user cannot toggle share on someone else's note."""
    note = create_note(client, auth_header, title="Private Formula")
    other_header = make_auth_header(client, "other_stylist_us8")

    res = client.patch(f"/api/notes/{note['id']}/share", json={"is_public": True}, headers=other_header)
    assert res.status_code == 403

    # Verify original owner's note remains private
    owner_notes = client.get("/api/notes", headers=auth_header).get_json()["notes"]
    target = [n for n in owner_notes if n["id"] == note["id"]]
    assert len(target) == 1
    assert target[0]["is_public"] is False


def test_share_note_missing_body(client, auth_header):
    """US-8: Missing is_public field returns 400."""
    note = create_note(client, auth_header, title="No Body Share")

    res = client.patch(f"/api/notes/{note['id']}/share", json={}, headers=auth_header)
    assert res.status_code == 400
    assert "is_public" in res.get_json()["error"].lower()


def test_share_note_unauthenticated(client, auth_header):
    """US-8: Unauthenticated request to share endpoint returns 401."""
    note = create_note(client, auth_header, title="Unauth Share")

    res = client.patch(f"/api/notes/{note['id']}/share", json={"is_public": True})
    assert res.status_code == 401


def test_feed_returns_only_public_notes(client, auth_header):
    """US-9: Feed returns only notes with is_public=True."""
    # Create private note
    create_note(client, auth_header, title="Private Formula", is_public=False)
    # Create public note
    create_note(client, auth_header, title="Public Formula", is_public=True)

    res = client.get("/api/notes/feed")
    assert res.status_code == 200
    notes = res.get_json()["notes"]
    assert len(notes) >= 1
    for n in notes:
        assert n["is_public"] is True
    titles = [n["title"] for n in notes]
    assert "Public Formula" in titles
    assert "Private Formula" not in titles

def test_feed_no_auth_required(client):
    """US-9: Feed endpoint does not require authentication."""
    res = client.get("/api/notes/feed")
    assert res.status_code == 200
    assert "notes" in res.get_json()

def test_feed_empty_when_no_public_notes(client, auth_header):
    """US-9: Feed returns empty list when no notes are public."""
    create_note(client, auth_header, title="Only Private", is_public=False)

    res = client.get("/api/notes/feed")
    assert res.status_code == 200
    assert res.get_json()["notes"] == []

def test_feed_ordered_newest_first(client, auth_header):
    """US-9: Feed returns notes ordered by created_at descending."""
    import time
    create_note(client, auth_header, title="Older Public", is_public=True)
    time.sleep(0.1)
    create_note(client, auth_header, title="Newer Public", is_public=True)

    res = client.get("/api/notes/feed")
    notes = res.get_json()["notes"]
    public_titles = [n["title"] for n in notes if n["title"] in ("Older Public", "Newer Public")]
    assert public_titles[0] == "Newer Public"
    assert public_titles[1] == "Older Public"
