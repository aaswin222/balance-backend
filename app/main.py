from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError

from .database import Base, engine
from .routers import auth, goals, transactions, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates tables if missing. It does NOT add new columns to tables that already exist
    # (e.g. users.password_hash), so after a model change run `docker compose down -v` once.
    # Alembic migrations would fix this properly (next step).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Balance Backend", version="0.2.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(goals.router)
app.include_router(transactions.router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    # Safety net: if a DB constraint (FK, CHECK, UNIQUE) catches something validation missed
    return JSONResponse(status_code=409, content={"detail": "Database constraint violated"})


@app.get("/", include_in_schema=False)
def root():
    # The bare URL used to return {"detail": "Not Found"}; send people to the interactive docs instead.
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
