from decimal import Decimal


# ---------- happy path: the demo scenario ----------
def test_spring_break_scenario(client, user):
    uid = user["id"]

    g = client.post(f"/users/{uid}/goals", json={"name": "Spring Break", "target_amount": 1000, "saved_amount": 250})
    assert g.status_code == 201
    assert g.json()["progress_pct"] == 25.0

    for amt, cat in [(15.50, "food"), (24.50, "food"), (12, "transportation")]:
        r = client.post(f"/users/{uid}/transactions", json={"amount": amt, "category": cat})
        assert r.status_code == 201

    s = client.get(f"/users/{uid}/spending-summary").json()
    totals = {row["category"]: Decimal(row["total"]) for row in s["by_category"]}
    assert totals == {"food": Decimal("40.00"), "transportation": Decimal("12.00")}
    assert Decimal(s["total_spending"]) == Decimal("52.00")


def test_filter_transactions_by_category(client, user):
    uid = user["id"]
    client.post(f"/users/{uid}/transactions", json={"amount": 5, "category": "food"})
    client.post(f"/users/{uid}/transactions", json={"amount": 9, "category": "school"})
    r = client.get(f"/users/{uid}/transactions", params={"category": "school"})
    assert [t["category"] for t in r.json()] == ["school"]


def test_update_and_delete_goal(client, user):
    uid = user["id"]
    gid = client.post(f"/users/{uid}/goals", json={"name": "Laptop", "target_amount": 800}).json()["id"]

    r = client.patch(f"/goals/{gid}", json={"saved_amount": 400})
    assert r.status_code == 200 and r.json()["progress_pct"] == 50.0

    assert client.delete(f"/goals/{gid}").status_code == 204
    assert client.get(f"/users/{uid}/goals").json() == []


def test_summary_date_range(client, user):
    uid = user["id"]
    client.post(f"/users/{uid}/transactions", json={"amount": 10, "category": "food", "occurred_on": "2026-01-05"})
    client.post(f"/users/{uid}/transactions", json={"amount": 99, "category": "food", "occurred_on": "2026-03-05"})
    s = client.get(f"/users/{uid}/spending-summary", params={"start": "2026-01-01", "end": "2026-01-31"}).json()
    assert Decimal(s["total_spending"]) == Decimal("10.00")


# ---------- error handling ----------
def test_duplicate_email_rejected(client, user):
    r = client.post("/users", json={"name": "Copy", "email": "aish@example.com"})
    assert r.status_code == 409


def test_negative_amount_rejected(client, user):
    r = client.post(f"/users/{user['id']}/transactions", json={"amount": -5, "category": "food"})
    assert r.status_code == 422


def test_invalid_category_rejected(client, user):
    r = client.post(f"/users/{user['id']}/transactions", json={"amount": 5, "category": "yachts"})
    assert r.status_code == 422


def test_saved_over_target_rejected(client, user):
    r = client.post(f"/users/{user['id']}/goals", json={"name": "X", "target_amount": 100, "saved_amount": 150})
    assert r.status_code == 422


def test_unknown_user_404(client):
    assert client.post("/users/999/transactions", json={"amount": 5, "category": "food"}).status_code == 404
    assert client.get("/users/999/spending-summary").status_code == 404


def test_bad_date_range_rejected(client, user):
    r = client.get(f"/users/{user['id']}/spending-summary", params={"start": "2026-02-01", "end": "2026-01-01"})
    assert r.status_code == 422
