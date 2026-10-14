"""
Login + privacy demo for Balance (Exercise 5).

Run while `docker compose up` is running:
    python3 scripts/auth_demo.py      (Mac/Linux)
    python  scripts/auth_demo.py      (Windows)

Standard library only, nothing to install. Creates two fresh accounts each run.
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
results = []


def call(method, path, body=None, token=None, form=None):
    headers = {}
    data = None
    if form is not None:  # /auth/login takes a form, like a real login page would send
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, (json.loads(raw) if raw else None)


def check(label, got, expected):
    ok = got == expected
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:<58} -> {got} (expected {expected})")


def section(title):
    print(f"\n{title}")


stamp = int(time.time())
SRIKAR = {"name": "Srikar", "email": f"srikar+{stamp}@example.com", "password": "balance-demo-123"}
ROOMIE = {"name": "Roommate", "email": f"roommate+{stamp}@example.com", "password": "roomie-secret-456"}

print("=" * 80)
print(f" Balance - login & privacy demo - {datetime.now():%Y-%m-%d %H:%M:%S} - {API}")
print("=" * 80)

section("1) Sign up two users (public: no login needed)")
st, srikar = call("POST", "/users", SRIKAR)
check(f"sign up {SRIKAR['email']}", st, 201)
check("password is NOT echoed back", "password" in json.dumps(srikar), False)
st, roomie = call("POST", "/users", ROOMIE)
check(f"sign up {ROOMIE['email']}", st, 201)

section("2) Log in")
st, _ = call("POST", "/auth/login", form={"username": SRIKAR["email"], "password": "wrong-password"})
check("Srikar logs in with the WRONG password", st, 401)
st, tok = call("POST", "/auth/login", form={"username": SRIKAR["email"], "password": SRIKAR["password"]})
check("Srikar logs in with the right password", st, 200)
srikar_token = tok["access_token"]
print(f"       token: {srikar_token[:40]}...")
st, tok = call("POST", "/auth/login", form={"username": ROOMIE["email"], "password": ROOMIE["password"]})
roomie_token = tok["access_token"]
st, me = call("GET", "/users/me", token=srikar_token)
check(f"GET /users/me with Srikar's token returns id {srikar['id']}", me["id"], srikar["id"])

section("3) No token = no data")
sid, rid = srikar["id"], roomie["id"]
st, _ = call("GET", f"/users/{sid}/transactions")
check(f"GET /users/{sid}/transactions with no token", st, 401)
st, _ = call("GET", "/users/me", token="made.up.token")
check("GET /users/me with a fake token", st, 401)

section("4) Each user records their own spending")
for amt, cat, desc in [(8.75, "food", "Panera"), (65, "school", "Textbook"), (14, "entertainment", "Movie")]:
    st, _ = call("POST", f"/users/{sid}/transactions", {"amount": amt, "category": cat, "description": desc}, srikar_token)
    check(f"Srikar adds {desc} ${amt}", st, 201)
st, _ = call("POST", f"/users/{rid}/transactions", {"amount": 1200, "category": "housing", "description": "Rent"}, roomie_token)
check("Roommate adds Rent $1200", st, 201)
st, goal = call("POST", f"/users/{rid}/goals", {"name": "Car", "target_amount": 5000, "saved_amount": 500}, roomie_token)
check("Roommate adds goal 'Car'", st, 201)

st, s = call("GET", f"/users/{sid}/spending-summary", token=srikar_token)
print("       Srikar's summary:", ", ".join(f"{r['category']} ${r['total']}" for r in s["by_category"]),
      f"| total ${s['total_spending']}")
check("Srikar's total excludes the roommate's rent", s["total_spending"], "87.75")

section("5) Srikar tries to reach the roommate's data")
st, _ = call("GET", f"/users/{rid}/transactions", token=srikar_token)
check(f"read roommate's transactions (/users/{rid}/transactions)", st, 403)
st, _ = call("GET", f"/users/{rid}/spending-summary", token=srikar_token)
check("read roommate's spending summary", st, 403)
st, _ = call("POST", f"/users/{rid}/transactions", {"amount": 1, "category": "other"}, srikar_token)
check("add a transaction to roommate's account", st, 403)
st, _ = call("PATCH", f"/goals/{goal['id']}", {"saved_amount": 0}, srikar_token)
check(f"edit roommate's goal (/goals/{goal['id']})", st, 404)
st, _ = call("DELETE", f"/users/{rid}", token=srikar_token)
check("delete roommate's account", st, 403)

st, g = call("GET", f"/users/{rid}/goals", token=roomie_token)
check("roommate's goal is untouched (saved $500.00)", g[0]["saved_amount"], "500.00")

print("\n" + "=" * 80)
print(f" {sum(results)}/{len(results)} checks passed")
print("=" * 80)
sys.exit(0 if all(results) else 1)
