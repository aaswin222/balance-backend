#!/usr/bin/env bash
# Runs the "Spring Break" demo scenario end-to-end against the running API.
set -euo pipefail
API=${API:-http://localhost:8000}
EMAIL="aishwarya+$(date +%s)@example.com"   # unique so re-runs don't hit the 409

echo "== 1. Create user"
UID_=$(curl -s -X POST "$API/users" -H 'Content-Type: application/json' \
  -d "{\"name\":\"Aishwarya\",\"email\":\"$EMAIL\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
echo "user_id=$UID_"

echo "== 2. Create Spring Break goal (\$1000 target, \$250 saved)"
curl -s -X POST "$API/users/$UID_/goals" -H 'Content-Type: application/json' \
  -d '{"name":"Spring Break","target_amount":1000,"saved_amount":250}'; echo

echo "== 3. Record three transactions"
for body in '{"amount":15.50,"category":"food","description":"Chipotle"}' \
            '{"amount":24.50,"category":"food","description":"Groceries"}' \
            '{"amount":12,"category":"transportation","description":"Uber"}'; do
  curl -s -X POST "$API/users/$UID_/transactions" -H 'Content-Type: application/json' -d "$body"; echo
done

echo "== 4. Spending summary (expect food 40.00, transportation 12.00, total 52.00)"
curl -s "$API/users/$UID_/spending-summary" | python3 -m json.tool

echo "== 5. Error handling: negative amount (expect 422)"
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$API/users/$UID_/transactions" \
  -H 'Content-Type: application/json' -d '{"amount":-5,"category":"food"}'

echo "== 6. Error handling: unknown user (expect 404)"
curl -s -o /dev/null -w "%{http_code}\n" "$API/users/999999/spending-summary"
