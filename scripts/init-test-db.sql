-- Runs once, the first time the Postgres volume is created (docker-entrypoint-initdb.d).
-- Gives pytest its own database so tests run on real Postgres without wiping demo data.
CREATE DATABASE balance_test;
