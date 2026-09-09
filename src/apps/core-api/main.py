import os
from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from routers import webhooks, redirects, ai, video_jobs, frontend_api
from services.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    enable_scheduler = os.getenv("ENABLE_BACKGROUND_SYNC", "true").lower() in ("true", "1")
    if enable_scheduler:
        start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(
    title="Shopify AI KOL Distribution OS - Core API",
    description="FastAPI Backend for Commerce, Ledger and AI Orchestration",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure media directory exists and mount static route for generated video assets
media_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../media/videos"))
os.makedirs(media_dir, exist_ok=True)
app.mount("/static/videos", StaticFiles(directory=media_dir), name="static_videos")

app.include_router(webhooks.router)
app.include_router(redirects.router)
app.include_router(ai.router)
app.include_router(video_jobs.router)
app.include_router(frontend_api.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "core-api"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
