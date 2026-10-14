# Balance Backend

ECE 49595 Senior Design I, Team 9
- Exercise 3 (Learn a Skill): Aishwarya Aswin — API, database, Docker
- Exercise 5 (Continue Another's Code): Srikar Mallajosyula — login, per-user privacy, secrets in `.env`, Postgres test DB

Demo video: https://drive.google.com/file/d/1FS2Sl2UYaGBzB9XbFDanGS3V8-E8i8E3/view

This is a small backend for Balance, our budgeting app. It stores users, savings goals, and transactions, and can give a spending summary by category. It's built with FastAPI and PostgreSQL, and both run in Docker containers.

Users sign up with a password and log in to get a token. Every data request must carry that token, and each user can only see and change their own data.

## Tools

- FastAPI for the API
- PostgreSQL for the database
- SQLAlchemy to talk to the database from Python (uses the psycopg2 driver)
- Pydantic to check incoming data
- Argon2 (via pwdlib) to hash passwords, PyJWT for login tokens
- Docker Compose to run the API and database together
- pytest for testing

## Database

There are 3 tables:

- users: id, name, email, password_hash, created_at
- goals: id, user_id, name, target_amount, saved_amount, deadline
- transactions: id, user_id, amount, category, description, occurred_on

user_id links each goal and transaction to a user.

## How to run

You need Docker Desktop open.

First time only, create your `.env` (it holds the passwords and is not committed):

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # paste the output as SECRET_KEY in .env
```

Then:

```bash
docker compose up --build
```

**Upgrading from the Exercise 3 version?** The `users` table gained a `password_hash` column, and the app can't add columns to an existing table. Run `docker compose down -v` once to start from a fresh database (this deletes old demo data).

Once it says `Uvicorn running on http://0.0.0.0:8000`, the API is up. It only runs locally on your computer.

## How to try it

- http://localhost:8000/docs lets you test every endpoint in the browser. Create a user with `POST /users`, then click **Authorize** (top right), enter the email as *username* plus the password, and the page sends your token on every request.
- `python3 scripts/auth_demo.py` signs up two users and shows login, 401 without a token, and 403/404 when one user goes after the other's data (20 checks)
- `./scripts/demo.sh` creates a user, logs in, adds a Spring Break goal and 3 purchases, then shows the spending summary (food $40, transportation $12, total $52)
- `docker compose exec api pytest -v` runs the 40 tests against a separate Postgres database (`balance_test`)
- `docker compose exec db psql -U balance -d balance` opens the database so you can run SQL queries (type `\q` to exit)

To stop it, run `docker compose down`. The data stays saved. Use `docker compose down -v` if you want to delete the data and start fresh.

## Endpoints

Public (no token): `POST /users`, `POST /auth/login`, `GET /health`. Everything else needs `Authorization: Bearer <token>`.

- POST /users - sign up (name, email, password of 8+ characters)
- POST /auth/login - log in with email + password (form fields `username`, `password`), returns a token valid for 60 minutes
- GET /users/me - the logged-in user
- GET /users/{id} - get a user
- DELETE /users/{id} - delete a user and their data
- POST /users/{id}/goals - create a goal
- GET /users/{id}/goals - list a user's goals
- PATCH /goals/{id} - update a goal
- DELETE /goals/{id} - delete a goal
- POST /users/{id}/transactions - add a transaction
- GET /users/{id}/transactions - list transactions (can filter by category)
- GET /users/{id}/spending-summary - totals by category (can filter by date)
- GET /health - check if the server is running

Bad requests return errors, like 422 for invalid data and 409 for a duplicate email.

Login and privacy errors:
- 401 - no token, an expired or fake token, or a wrong email/password (same message for both, so it doesn't reveal which emails exist)
- 403 - a `/users/{id}/...` URL with someone else's id (same for ids that don't exist, so ids can't be probed)
- 404 - a `/goals/{id}` that belongs to someone else (looks the same as a missing goal)

## Files

- `.env.example` template for the secrets file (`.env`, not committed)
- `docker-compose.yml` starts the database and API containers, reading secrets from `.env`
- `Dockerfile` builds the API container
- `requirements.txt` lists the Python packages
- `app/main.py` starts the app and creates the tables
- `app/database.py` connects to Postgres
- `app/config.py` reads the secret key and token lifetime from the environment
- `app/security.py` hashes passwords and creates/checks login tokens
- `app/deps.py` finds the logged-in user from the token and blocks access to other users' data
- `app/models.py` defines the 3 tables
- `app/schemas.py` defines what valid input looks like
- `app/routers/` has the endpoints for auth, users, goals, and transactions
- `tests/` has the automated tests: `test_api.py` (original features), `test_auth.py` (login), `test_privacy.py` (users can't reach each other's data)
- `scripts/` has the demo scripts, SQL queries for checking the database, and `init-test-db.sql` (creates the test database)

## Next steps

- ~~Add login so users can only see their own data~~ (done in Exercise 5)
- ~~Move passwords out of the config file~~ (done in Exercise 5)
- Use migrations (Alembic) so schema changes like `password_hash` don't need `down -v`, then add budgets and paydays
- Rate-limit `/auth/login`, and add refresh tokens / logout
- Deploy to AWS (secrets from AWS Secrets Manager instead of `.env`)

## GenAI usage

Exercise 3: The starter code, tests, scripts, and README were generated with Claude. I set up the repo, ran and debugged it on my machine, tested the endpoints and error cases, and recorded the demo. (Aishwarya)

Exercise 5: The first draft of the login, privacy, test, and demo-script changes was generated with Claude. I reviewed it, built and tested it on my machine, and committed it in steps. (Srikar)
