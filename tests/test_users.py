# tests/test_users.py
import pytest


def user_payload(
    first_name="Nathan",
    last_name="McCormack",
    email="nathan.mccormack@atu.ie",
    phone="+353 091 123 4567",
    age=21,
    sid="G00123456",
):
    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "age": age,
        "student_id": sid,
    }


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "users"}


def test_list_users_empty_ok(client):
    r = client.get("/api/users")
    assert r.status_code == 200
    assert r.json() == []


def test_create_user_ok(client):
    r = client.post("/api/users", json=user_payload())
    assert r.status_code == 201
    data = r.json()

    assert "id" in data
    assert data["first_name"] == "Nathan"
    assert data["last_name"] == "McCormack"
    assert data["age"] == 21
    assert data["student_id"] == "G00123456"


def test_list_users_after_create_ok(client):
    client.post("/api/users", json=user_payload(email="nathan1@atu.ie", sid="G00123457", phone="+353 091 123 4568"))
    client.post("/api/users", json=user_payload(email="nathan2@atu.ie", sid="G00123458", phone="+353 091 123 4569"))

    r = client.get("/api/users")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) == 2


def test_get_user_ok(client):
    created = client.post(
        "/api/users",
        json=user_payload(email="nathan.get@atu.ie", sid="G00123459", phone="+353 091 111 2222"),
    ).json()
    uid = created["id"]

    r = client.get(f"/api/users/{uid}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == uid
    assert body["first_name"] == "Nathan"
    assert body["last_name"] == "McCormack"


def test_get_user_404(client):
    r = client.get("/api/users/999999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_patch_user_ok(client):
    created = client.post(
        "/api/users",
        json=user_payload(email="nathan.patch@atu.ie", sid="G00123460", phone="+353 091 222 3333"),
    ).json()
    uid = created["id"]

    r = client.patch(f"/api/users/{uid}", json={"age": 22})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == uid
    assert body["age"] == 22


def test_patch_user_404(client):
    r = client.patch("/api/users/999999", json={"age": 22})
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_put_replace_user_ok(client):
    created = client.post(
        "/api/users",
        json=user_payload(email="nathan.put@atu.ie", sid="G00123461", phone="+353 091 333 4444"),
    ).json()
    uid = created["id"]

    updated = user_payload(
        email="nathan.updated@atu.ie",
        phone="+353 091 444 5555",
        age=23,
        sid="G00999999",
    )
    r = client.put(f"/api/users/{uid}", json=updated)
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == uid
    assert body["email"] == "nathan.updated@atu.ie"
    assert body["phone"] == "+353 091 444 5555"
    assert body["age"] == 23
    assert body["student_id"] == "G00999999"


def test_put_missing_user_404(client):
    r = client.put("/api/users/999999", json=user_payload())
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_delete_then_404(client):
    created = client.post(
        "/api/users",
        json=user_payload(email="nathan.del@atu.ie", sid="G00123462", phone="+353 091 555 6666"),
    ).json()
    uid = created["id"]

    r1 = client.delete(f"/api/users/{uid}")
    assert r1.status_code == 204

    r2 = client.delete(f"/api/users/{uid}")
    assert r2.status_code == 404
    assert "not found" in r2.json()["detail"].lower()


# --- 409 tests based on UNIQUE constraints (email / phone / student_id) ---

def test_duplicate_email_conflict_409(client):
    client.post("/api/users", json=user_payload(email="dup@atu.ie", sid="G00123463", phone="+353 091 777 1111"))
    r = client.post("/api/users", json=user_payload(email="dup@atu.ie", sid="G00123464", phone="+353 091 777 2222"))
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"].lower()


def test_patch_to_existing_email_conflict_409(client):
    u1 = client.post(
        "/api/users",
        json=user_payload(email="first@atu.ie", sid="G00123465", phone="+353 091 888 1111"),
    ).json()
    u2 = client.post(
        "/api/users",
        json=user_payload(email="second@atu.ie", sid="G00123466", phone="+353 091 888 2222"),
    ).json()

    r = client.patch(f"/api/users/{u2['id']}", json={"email": "first@atu.ie"})
    assert r.status_code == 409
    assert "unique" in r.json()["detail"].lower() or "failed" in r.json()["detail"].lower()


def test_put_to_existing_student_id_conflict_409(client):
    u1 = client.post(
        "/api/users",
        json=user_payload(email="sid1@atu.ie", sid="G00123467", phone="+353 091 999 1111"),
    ).json()
    u2 = client.post(
        "/api/users",
        json=user_payload(email="sid2@atu.ie", sid="G00123468", phone="+353 091 999 2222"),
    ).json()

    updated = user_payload(email="sid2.new@atu.ie", sid=u1["student_id"], phone="+353 091 999 3333")
    r = client.put(f"/api/users/{u2['id']}", json=updated)
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"].lower()


# --- 422 validation tests (schema-driven) ---

@pytest.mark.parametrize("bad_sid", ["BAD123", "G00123", "G0012345", "g00123456", ""])
def test_create_user_bad_student_id_422(client, bad_sid):
    r = client.post(
        "/api/users",
        json=user_payload(email="bad.sid@atu.ie", sid=bad_sid, phone="+353 091 101 2020"),
    )
    assert r.status_code == 422


@pytest.mark.parametrize("bad_phone", [
    "0851234567",
    "+3530911234567",
    "+353 91 123 4567",
    "+353 091 12 4567",
    "+353 091 1234 567",
    "",
])
def test_create_user_bad_phone_422(client, bad_phone):
    r = client.post(
        "/api/users",
        json=user_payload(email="bad.phone@atu.ie", sid="G00123470", phone=bad_phone),
    )
    assert r.status_code == 422


@pytest.mark.parametrize("bad_email", ["not-an-email", "nathan@", "@atu.ie", "x@.com", ""])
def test_create_user_bad_email_422(client, bad_email):
    r = client.post(
        "/api/users",
        json=user_payload(email=bad_email, sid="G00123471", phone="+353 091 303 4040"),
    )
    assert r.status_code == 422


@pytest.mark.parametrize("bad_age", [15, 101])
def test_create_user_bad_age_422(client, bad_age):
    r = client.post(
        "/api/users",
        json=user_payload(email="bad.age@atu.ie", sid="G00123472", phone="+353 091 505 6060", age=bad_age),
    )
    assert r.status_code == 422
