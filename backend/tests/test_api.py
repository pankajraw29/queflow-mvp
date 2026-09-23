"""End-to-end API tests against an in-memory fake MongoDB."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.db import get_db
from app.main import create_app
from tests.fake_db import FakeDB

EMAIL = "owner@example.com"
PASSWORD = "secret123"


@pytest.fixture()
def app():
    application = create_app()
    db = FakeDB()  # one shared DB for the whole test
    application.dependency_overrides[get_db] = lambda: db
    return application


@pytest.fixture()
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


async def register(client, email=EMAIL, password=PASSWORD, business="Acme Clinic"):
    r = await client.post(
        "/api/auth/register",
        json={
            "name": "Owner",
            "email": email,
            "password": password,
            "business_name": business,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


async def auth_headers(client):
    data = await register(client)
    return {"Authorization": f"Bearer {data['access_token']}"}


async def test_health(client):
    r = await client.get("/api/health")
    assert r.json() == {"ok": True}


async def test_register_login_me(client):
    data = await register(client)
    assert data["business"]["email"] == EMAIL
    assert "password_hash" not in str(data)

    # duplicate email rejected
    r = await client.post(
        "/api/auth/register",
        json={"name": "X", "email": EMAIL, "password": PASSWORD, "business_name": "Y"},
    )
    assert r.status_code == 400

    # login works
    r = await client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert r.status_code == 200
    token = r.json()["access_token"]

    # wrong password rejected
    r = await client.post(
        "/api/auth/login", json={"email": EMAIL, "password": "wrongpass"}
    )
    assert r.status_code == 401

    # me works
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["business_name"] == "Acme Clinic"

    # bad token rejected
    r = await client.get("/api/auth/me", headers={"Authorization": "Bearer junk"})
    assert r.status_code == 401


async def test_protected_routes_need_auth(client):
    assert (await client.get("/api/queues")).status_code in (401, 403)
    assert (await client.post("/api/queues", json={"name": "Q"})).status_code in (401, 403)


async def test_full_queue_flow(client):
    headers = await auth_headers(client)

    # create queue
    r = await client.post("/api/queues", json={"name": "General"}, headers=headers)
    assert r.status_code == 201, r.text
    queue = r.json()
    qid, code = queue["id"], queue["code"]
    assert len(code) >= 4

    # customers join via public link
    names = ["Asha", "Ravi", "Meena"]
    tickets = []
    for i, name in enumerate(names):
        r = await client.post(f"/api/pub/q/{code}/join", json={"customer_name": name})
        assert r.status_code == 201, r.text
        body = r.json()
        tickets.append(body)
        assert body["number"] == f"A{i + 1:02d}"
        assert body["position"] == i + 1

    # queue detail shows ordered tickets
    r = await client.get(f"/api/queues/{qid}", headers=headers)
    assert r.status_code == 200
    got = r.json()["tickets"]
    assert [t["number"] for t in got] == ["A01", "A02", "A03"]
    assert all(t["status"] == "waiting" for t in got)

    # public info
    r = await client.get(f"/api/pub/q/{code}")
    assert r.json()["waiting_count"] == 3

    # ticket status polling: 3rd ticket sees 2 ahead
    r = await client.get(f"/api/pub/q/{code}/t/{tickets[2]['ticket_id']}")
    body = r.json()
    assert body["status"] == "waiting" and body["ahead_count"] == 2

    # call next -> A01 serving
    r = await client.post(f"/api/queues/{qid}/call-next", headers=headers)
    assert r.status_code == 200
    assert r.json()["number"] == "A01"

    # cannot call next while one is serving
    r = await client.post(f"/api/queues/{qid}/call-next", headers=headers)
    assert r.status_code == 409

    # A01 now sees "your turn"
    r = await client.get(f"/api/pub/q/{code}/t/{tickets[0]['ticket_id']}")
    assert r.json()["status"] == "serving"

    # complete current, call next -> A02
    r = await client.post(f"/api/queues/{qid}/complete-current", headers=headers)
    assert r.json()["status"] == "done"
    r = await client.post(f"/api/queues/{qid}/call-next", headers=headers)
    assert r.json()["number"] == "A02"

    # skip current -> A02 skipped
    r = await client.post(f"/api/queues/{qid}/skip-current", headers=headers)
    assert r.json()["status"] == "skipped"

    # A03 still waiting with 0 ahead
    r = await client.get(f"/api/pub/q/{code}/t/{tickets[2]['ticket_id']}")
    assert r.json()["ahead_count"] == 0

    # close queue -> join rejected
    r = await client.patch(f"/api/queues/{qid}", json={"is_open": False}, headers=headers)
    assert r.json()["is_open"] is False
    r = await client.post(f"/api/pub/q/{code}/join", json={"customer_name": "Late"})
    assert r.status_code == 410

    # reset clears everything and restarts numbering
    r = await client.post(f"/api/queues/{qid}/reset", headers=headers)
    assert r.json()["ok"] is True
    r = await client.patch(f"/api/queues/{qid}", json={"is_open": True}, headers=headers)
    r = await client.post(f"/api/pub/q/{code}/join", json={"customer_name": "New"})
    assert r.json()["number"] == "A01"

    # delete queue
    r = await client.delete(f"/api/queues/{qid}", headers=headers)
    assert r.status_code == 204
    r = await client.get(f"/api/queues/{qid}", headers=headers)
    assert r.status_code == 404


async def test_owner_isolation(client):
    h1 = await auth_headers(client)
    r = await client.post("/api/queues", json={"name": "Q1"}, headers=h1)
    qid = r.json()["id"]

    # second business cannot see / touch the first business's queue
    data2 = await register(client, email="other@example.com", business="Other")
    h2 = {"Authorization": f"Bearer {data2['access_token']}"}
    assert (await client.get(f"/api/queues/{qid}", headers=h2)).status_code == 404
    assert (await client.post(f"/api/queues/{qid}/call-next", headers=h2)).status_code == 404
    r = await client.get("/api/queues", headers=h2)
    assert r.json() == []
