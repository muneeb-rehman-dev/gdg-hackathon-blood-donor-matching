from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api import chat, donors, requests, dashboard, ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Blood Donor Matching API",
    description="AI-powered emergency blood donor matching system for Karachi",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(donors.router)
app.include_router(requests.router)
app.include_router(dashboard.router)
app.include_router(ws.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "blood-donor-matching"}
