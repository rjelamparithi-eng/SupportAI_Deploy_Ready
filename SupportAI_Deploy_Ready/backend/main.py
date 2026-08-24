import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import analytics, auth, business, chat
from app.utils.database import close_db, connect_db

app = FastAPI(
    title="AI Customer Support SaaS",
    version="1.0.0",
)

# Comma-separated list, e.g.
# CORS_ORIGINS=http://localhost:3000,https://support-ai.vercel.app
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await connect_db()


@app.on_event("shutdown")
async def shutdown():
    await close_db()


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(business.router, prefix="/api/business", tags=["business"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


@app.get("/")
async def root():
    return {"message": "AI Customer Support API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
