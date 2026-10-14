#!/usr/bin/env bash
# Runs the "Spring Break" demo scenario end-to-end against the running API.
# Updated in Exercise 5: sign-up now needs a password, and every data request needs a login token.
set -euo pipefail
API=${API:-http://localhost:8000}
EMAIL="aishwarya+$(date +%s)@example.com"   # unique so re-runs don't hit the 409
PASSWORD="spring-break-2026"

echo "== 1. Create user"
UID_=$(curl -s -X POST "$API/users" -H 'Content-Type: application/json' \
  -d "{\"name\":\"Aishwarya\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
echo "user_id=$UID_"

echo "== 2. Log in and keep the token"
# --data-urlencode matters: in a form body a raw "+" in the email would turn into a space.
TOKEN=$(curl -s -X POST "$API/auth/login" --data-urlencode "username=$EMAIL" --data-urlencode "password=$PASSWORD" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
AUTH="Authorization: Bearer $TOKEN"
echo "token=${TOKEN:0:30}..."

echo "== 3. Create Spring Break goal (\$1000 target, \$250 saved)"
curl -s -X POST "$API/users/$UID_/goals" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"name":"Spring Break","target_amount":1000,"saved_amount":250}'; echo

echo "== 4. Record three transactions"
for body in '{"amount":15.50,"category":"food","description":"Chipotle"}' \
            '{"amount":24.50,"category":"food","description":"Groceries"}' \
            '{"amount":12,"category":"transportation","description":"Uber"}'; do
  curl -s -X POST "$API/users/$UID_/transactions" -H "$AUTH" -H 'Content-Type: application/json' -d "$body"; echo
done

echo "== 5. Spending summary (expect food 40.00, transportation 12.00, total 52.00)"
curl -s "$API/users/$UID_/spending-summary" -H "$AUTH" | python3 -m json.tool

echo "== 6. Error handling: negative amount (expect 422)"
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$API/users/$UID_/transactions" -H "$AUTH" \
  -H 'Content-Type: application/json' -d '{"amount":-5,"category":"food"}'

echo "== 7. Privacy: no token (expect 401)"
curl -s -o /dev/null -w "%{http_code}\n" "$API/users/$UID_/spending-summary"

echo "== 8. Privacy: someone else's user id (expect 403)"
curl -s -o /dev/null -w "%{http_code}\n" "$API/users/999999/spending-summary" -H "$AUTH"
