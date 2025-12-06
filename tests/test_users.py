import pytest 
from fastapi.testclient import TestClient 
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker 
from sqlalchemy.pool import StaticPool
 
from app.main import app, get_db 
from app.models import Base 
 
TEST_DB_URL = "sqlite+pysqlite:///:memory:" 
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool) 
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False) 
Base.metadata.create_all(bind=engine) 
 
@pytest.fixture 
def client(): 
    def override_get_db(): 
        db = TestingSessionLocal() 
        try: 
            yield db 
        finally: 
            db.close() 
    app.dependency_overrides[get_db] = override_get_db 
    with TestClient(app) as c: 
        # hand the client to the test 
        yield c 
        # --- teardown happens when the 'with' block exits --- 
        #  

 #-------------- User Tests -----------------
def test_create_user(client): 
    r = client.post("/api/users", json={"first_name":"Darragh","last_name":"McCormack","email":"Darragh@atu.ie", "phone":"+353 083 555 5555","age":21,"student_id":"G00123456"}) 
    assert r.status_code == 201 

def test_patch_user_success(client):
    create = client.post(
        "/api/users",
        json={"first_name": "Alice","last_name": "McCormack", "email": "alice@ex.com","phone":"+353 083 559 5555", "age": 21, "student_id": "G00123486"},
    )
    assert create.status_code == 201, create.text
    u = create.json()  # <-- parse JSON body

    r = client.patch(f"/api/users/{u['id']}", json={"first_name": "AliceUpdated"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == u["id"]
    assert body["first_name"] == "AliceUpdated"
    assert body["last_name"] == "McCormack"    # unchanged
    assert body["email"] == "alice@ex.com"     # unchanged
    assert body["phone"] == "+353 083 559 5555" # unchanged
    assert body["age"] == 21                   # unchanged
    assert body["student_id"] == "G00123486"    # unchanged

def test_put_user_full_update_success(client):
    create = client.post(
        "/api/users",
        json={"first_name":"Darragh","last_name":"McCormack","email":"Darragh1@atu.ie", "phone":"+353 083 155 5555","age":21,"student_id":"G00123451"}
    )
    assert create.status_code == 201, create.text
    u = create.json()

    payload = {
        "first_name": "Mike",
        "last_name": "Dull",
        "email": "mike@gmail.com",
        "phone": "+353 091 555 5555",
        "age": 25,
        "student_id": "G00414785",
    }
    r = client.put(f"/api/users/{u['id']}", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["first_name"] == "Mike"
    assert body["last_name"] == "Dull"    # unchanged
    assert body["email"] == "mike@gmail.com"     # unchanged
    assert body["phone"] == "+353 091 555 5555" # unchanged
    assert body["age"] == 25                    # unchanged
    assert body["student_id"] == "G00414785"    # unchanged

def test_put_user_not_found(client):
    payload = {
        "first_name": "Ghost",
        "last_name": "Cas[er]",
        "email": "no@gmail.com",
        "phone": "+353 055 555 5555",
        "age": 25,
        "student_id": "G00414555",
    }
    r = client.put("/api/users/424242", json=payload)
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


