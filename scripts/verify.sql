-- Run with: docker compose exec -T db psql -U balance -d balance < scripts/verify.sql

\echo '--- users ---'
SELECT id, name, email FROM users ORDER BY id;

\echo '--- goals joined to owner ---'
SELECT g.id, u.name AS owner, g.name, g.target_amount, g.saved_amount
FROM goals g JOIN users u ON u.id = g.user_id ORDER BY g.id;

\echo '--- transactions joined to owner ---'
SELECT t.id, u.name AS owner, t.amount, t.category, t.description, t.occurred_on
FROM transactions t JOIN users u ON u.id = t.user_id ORDER BY t.id;

\echo '--- same aggregation the API does (should match /spending-summary) ---'
SELECT user_id, category, SUM(amount) AS total, COUNT(*) AS n
FROM transactions GROUP BY user_id, category ORDER BY user_id, total DESC;

\echo '--- constraints Postgres enforces (FKs + CHECKs) ---'
SELECT conrelid::regclass AS table, conname, pg_get_constraintdef(oid)
FROM pg_constraint WHERE conrelid::regclass::text IN ('goals','transactions') ORDER BY 1,2;
