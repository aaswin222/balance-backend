# Balance Backend

ECE 49595 Senior Design I, Exercise 3 (Learn a Skill), Team 9
Aishwarya Aswin

Demo video: [add link here]

This is a small backend for Balance, our budgeting app. It stores users, savings goals, and transactions, and can give a spending summary by category. It's built with FastAPI and PostgreSQL, and both run in Docker containers.

## Tools

- FastAPI for the API
- PostgreSQL for the database
- SQLAlchemy to talk to the database from Python (uses the psycopg2 driver)
- Pydantic to check incoming data
- Docker Compose to run the API and database together
- pytest for testing

## Database

There are 3 tables:

- users: id, name, email, created_at
- goals: id, user_id, name, target_amount, saved_amount, deadline
- transactions: id, user_id, amount, category, description, occurred_on

user_id links each goal and transaction to a user.

## How to run

You need Docker Desktop open.

```bash
docker compose up --build
```

Once it says `Uvicorn running on http://0.0.0.0:8000`, the API is up. It only runs locally on your computer.

## How to try it

- http://localhost:8000/docs lets you test every endpoint in the browser
- `./scripts/demo.sh` creates a user, a Spring Break goal, and 3 purchases, then shows the spending summary (food $40, transportation $12, total $52)
- `docker compose exec api pytest -v` runs the 10 tests
- `docker compose exec db psql -U balance -d balance` opens the database so you can run SQL queries (type `\q` to exit)

To stop it, run `docker compose down`. The data stays saved. Use `docker compose down -v` if you want to delete the data and start fresh.

## Endpoints

- POST /users - create a user
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

Bad requests return errors, like 422 for invalid data, 404 if the user doesn't exist, and 409 for a duplicate email.

## Files

- `docker-compose.yml` starts the database and API containers
- `Dockerfile` builds the API container
- `requirements.txt` lists the Python packages
- `app/main.py` starts the app and creates the tables
- `app/database.py` connects to Postgres
- `app/models.py` defines the 3 tables
- `app/schemas.py` defines what valid input looks like
- `app/routers/` has the endpoints for users, goals, and transactions
- `tests/` has the automated tests
- `scripts/` has the demo script and SQL queries for checking the database

## Next steps

- Add login so users can only see their own data
- Use migrations (Alembic) to add tables like budgets and paydays without losing data
- Move passwords out of the config file
- Deploy to AWS

## GenAI usage

The starter code, tests, scripts, and README were generated with Claude. I set up the repo, ran and debugged it on my machine, tested the endpoints and error cases, and recorded the demo.
