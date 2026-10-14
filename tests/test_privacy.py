"""One user must never be able to see or change another user's data (added in Exercise 5).

Setup for every test: Srikar and Aishwarya each have an account. Aishwarya has a goal and
a transaction. Srikar is logged in and tries to reach her data.
"""
import pytest

from .conftest import signup_and_login


@pytest.fixture()
def two_users(client):
    srikar, srikar_h = signup_and_login(client, "Srikar", "srikar@example.com")
    aish, aish_h = signup_and_login(client, "Aishwarya", "aish@example.com")
    goal = client.post(f"/users/{aish['id']}/goals", headers=aish_h,
                       json={"name": "Spring Break", "target_amount": 1000}).json()
    client.post(f"/users/{aish['id']}/transactions", headers=aish_h,
                json={"amount": 15.5, "category": "food", "description": "Chipotle"})
    return {"srikar": srikar, "srikar_h": srikar_h, "aish": aish, "aish_h": aish_h, "goal": goal}


# ---------- no token at all ----------
@pytest.mark.parametrize("method,path", [
    ("get", "/users/1"),
    ("delete", "/users/1"),
    ("get", "/users/1/goals"),
    ("post", "/users/1/goals"),
    ("patch", "/goals/1"),
    ("delete", "/goals/1"),
    ("get", "/users/1/transactions"),
    ("post", "/users/1/transactions"),
    ("get", "/users/1/spending-summary"),
])
def test_every_data_route_needs_login(client, method, path):
    assert getattr(client, method)(path).status_code == 401


def test_public_routes_still_open(client):
    assert client.get("/health").status_code == 200
    r = client.post("/users", json={"name": "New", "email": "new@example.com", "password": "long-enough-pw"})
    assert r.status_code == 201  # sign-up has to work without being logged in


# ---------- logged in as Srikar, going after Aishwarya's data ----------
def test_cannot_read_other_users_transactions(client, two_users):
    r = client.get(f"/users/{two_users['aish']['id']}/transactions", headers=two_users["srikar_h"])
    assert r.status_code == 403


def test_cannot_read_other_users_spending_summary(client, two_users):
    r = client.get(f"/users/{two_users['aish']['id']}/spending-summary", headers=two_users["srikar_h"])
    assert r.status_code == 403


def test_cannot_read_other_users_goals_or_profile(client, two_users):
    aid, h = two_users["aish"]["id"], two_users["srikar_h"]
    assert client.get(f"/users/{aid}/goals", headers=h).status_code == 403
    assert client.get(f"/users/{aid}", headers=h).status_code == 403


def test_cannot_add_transaction_to_other_user(client, two_users):
    aid = two_users["aish"]["id"]
    r = client.post(f"/users/{aid}/transactions", headers=two_users["srikar_h"],
                    json={"amount": 999, "category": "other"})
    assert r.status_code == 403
    # and nothing was written to her account
    mine = client.get(f"/users/{aid}/transactions", headers=two_users["aish_h"]).json()
    assert [t["amount"] for t in mine] == ["15.50"]


def test_cannot_edit_or_delete_other_users_goal(client, two_users):
    gid, h = two_users["goal"]["id"], two_users["srikar_h"]
    assert client.patch(f"/goals/{gid}", headers=h, json={"saved_amount": 1000}).status_code == 404
    assert client.delete(f"/goals/{gid}", headers=h).status_code == 404
    # her goal is untouched
    goals = client.get(f"/users/{two_users['aish']['id']}/goals", headers=two_users["aish_h"]).json()
    assert goals[0]["saved_amount"] == "0.00"


def test_cannot_delete_other_user_account(client, two_users):
    aid = two_users["aish"]["id"]
    assert client.delete(f"/users/{aid}", headers=two_users["srikar_h"]).status_code == 403
    assert client.get("/users/me", headers=two_users["aish_h"]).status_code == 200  # still exists


def test_each_user_sees_only_their_own_transactions(client, two_users):
    sid, sh = two_users["srikar"]["id"], two_users["srikar_h"]
    client.post(f"/users/{sid}/transactions", headers=sh, json={"amount": 65, "category": "school"})
    mine = client.get(f"/users/{sid}/transactions", headers=sh).json()
    assert [t["user_id"] for t in mine] == [sid]
    summary = client.get(f"/users/{sid}/spending-summary", headers=sh).json()
    assert summary["total_spending"] == "65.00"  # her $15.50 is not mixed in


def test_deleted_users_token_stops_working(client, two_users):
    sid, sh = two_users["srikar"]["id"], two_users["srikar_h"]
    assert client.delete(f"/users/{sid}", headers=sh).status_code == 204
    assert client.get("/users/me", headers=sh).status_code == 401
