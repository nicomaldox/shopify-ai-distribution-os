from fastapi import FastAPI
import uvicorn
from routers import webhooks, redirects, ai

app = FastAPI(
    title="Shopify AI KOL Distribution OS - Core API",
    description="FastAPI Backend for Commerce, Ledger and AI Orchestration",
    version="0.1.0"
)

app.include_router(webhooks.router)
app.include_router(redirects.router)
app.include_router(ai.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "core-api"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
