# tests/test_addresses.py
import pytest


# address_line2 uses AddrStr(min_length=3)
GALWAY_TOWNS = [
    "Salthill",      
    "Oranmore",      
    "Loughrea",     
    "Headford",      
    "Portumna",     
    "Ballinasloe",  
    "Ballinderreen",
    "Williamstown", 
]


def user_payload(
    first_name="Nathan",
    last_name="McCormack",
    email="nathan.address@atu.ie",
    phone="+353 091 707 8080",
    age=21,
    sid="G00130000",
):
    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "age": age,
        "student_id": sid,
    }


def address_payload(
    resident_id: int,
    town="Salthill",
    post_code="H91AB12",
    apt=12,
):
    return {
        "address_line1": "Galway City",
        "address_line2": town,
        "apartment_block_number": apt,
        "county": "Galway",
        "post_code": post_code,
        "resident_id": resident_id,
    }


def test_list_addresses_empty_ok(client):
    r = client.get("/api/addresses")
    assert r.status_code == 200
    assert r.json() == []


def test_create_address_user_missing_404(client):
    r = client.post("/api/addresses", json=address_payload(resident_id=999999, town="Salthill"))
    assert r.status_code == 404
    assert "user not found" in r.json()["detail"].lower()


@pytest.mark.parametrize("town", GALWAY_TOWNS)
def test_create_address_ok_galway_towns(client, town):
    idx = GALWAY_TOWNS.index(town)

    u = client.post(
        "/api/users",
        json=user_payload(
            email=f"nathan.{town.lower()}@atu.ie",
            sid=f"G00{130001 + idx:06d}",
            phone=f"+353 091 {700 + idx:03d} {1000 + idx:04d}",
        ),
    ).json()

    r = client.post("/api/addresses", json=address_payload(resident_id=u["id"], town=town))
    assert r.status_code == 201
    body = r.json()
    assert body["address_line1"] == "Galway City"
    assert body["address_line2"] == town
    assert body["county"] == "Galway"
    assert body["resident_id"] == u["id"]


def test_get_address_ok_with_owner(client):
    u = client.post(
        "/api/users",
        json=user_payload(email="nathan.owner@atu.ie", sid="G00130050", phone="+353 091 111 2222"),
    ).json()
    a = client.post("/api/addresses", json=address_payload(resident_id=u["id"], town="Oranmore")).json()

    r = client.get(f"/api/addresses/{a['id']}")
    assert r.status_code == 200
    body = r.json()

    assert body["id"] == a["id"]
    assert body["address_line1"] == "Galway City"
    assert body["resident_id"] == u["id"]

    # AddressReadWithOwner includes resident (UserRead)
    assert "resident" in body
    assert body["resident"] is not None
    assert body["resident"]["id"] == u["id"]
    assert body["resident"]["first_name"] == "Nathan"
    assert body["resident"]["last_name"] == "McCormack"


def test_get_address_404(client):
    r = client.get("/api/addresses/999999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_patch_address_ok(client):
    u = client.post(
        "/api/users",
        json=user_payload(email="nathan.patchaddr@atu.ie", sid="G00130060", phone="+353 091 333 4444"),
    ).json()
    a = client.post("/api/addresses", json=address_payload(resident_id=u["id"], town="Salthill")).json()

    r = client.patch(f"/api/addresses/{a['id']}", json={"address_line2": "Ballinasloe"})
    assert r.status_code == 200
    assert r.json()["address_line2"] == "Ballinasloe"


def test_patch_address_404(client):
    r = client.patch("/api/addresses/999999", json={"county": "Galway"})
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_put_address_ok(client):
    u = client.post(
        "/api/users",
        json=user_payload(email="nathan.putaddr@atu.ie", sid="G00130070", phone="+353 091 555 6666"),
    ).json()
    a = client.post("/api/addresses", json=address_payload(resident_id=u["id"], town="Loughrea", post_code="H91AB12")).json()

    updated = address_payload(resident_id=u["id"], town="Headford", post_code="D02X285", apt=99)
    r = client.put(f"/api/addresses/{a['id']}", json=updated)
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == a["id"]
    assert body["address_line2"] == "Headford"
    assert body["post_code"] == "D02X285"
    assert body["apartment_block_number"] == 99


def test_put_address_404(client):
    r = client.put("/api/addresses/999999", json=address_payload(resident_id=1, town="Salthill"))
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_delete_user_cascades_address_delete(client):
    u = client.post(
        "/api/users",
        json=user_payload(email="nathan.cascade@atu.ie", sid="G00130080", phone="+353 091 777 8888"),
    ).json()
    a = client.post("/api/addresses", json=address_payload(resident_id=u["id"], town="Portumna")).json()

    r_del = client.delete(f"/api/users/{u['id']}")
    assert r_del.status_code == 204

    r_get = client.get(f"/api/addresses/{a['id']}")
    assert r_get.status_code == 404


# --- 422 validation tests for addresses ---

@pytest.mark.parametrize("bad_post_code", ["badcode", "D0 2X285", "D02X28", "D02X2855", ""])
def test_create_address_bad_post_code_422(client, bad_post_code):
    u = client.post(
        "/api/users",
        json=user_payload(email="nathan.badpc@atu.ie", sid="G00130100", phone="+353 091 121 3434"),
    ).json()

    r = client.post("/api/addresses", json=address_payload(resident_id=u["id"], town="Oranmore", post_code=bad_post_code))
    assert r.status_code == 422


def test_create_address_line2_too_short_422(client):
    u = client.post(
        "/api/users",
        json=user_payload(email="nathan.shorttown@atu.ie", sid="G00130101", phone="+353 091 565 6565"),
    ).json()

    r = client.post("/api/addresses", json=address_payload(resident_id=u["id"], town="Ba"))
    assert r.status_code == 422
