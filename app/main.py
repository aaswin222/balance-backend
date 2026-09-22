from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from .database import Base, engine
from .routers import goals, transactions, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates tables if missing. Fine for a prototype; swap for Alembic migrations later.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Balance Backend", version="0.1.0", lifespan=lifespan)
app.include_router(users.router)
app.include_router(goals.router)
app.include_router(transactions.router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    # Safety net: if a DB constraint (FK, CHECK, UNIQUE) catches something validation missed
    return JSONResponse(status_code=409, content={"detail": "Database constraint violated"})


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
