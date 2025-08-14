# app/main.py
from fastapi import FastAPI, Depends
from .logging import init_logging
from .auth import basic_auth
from app.core.config import settings

init_logging()

app = FastAPI(title=settings.app_name, version="0.1.0")

@app.get("/healthz")
def health_check_auth(auth: bool = Depends(basic_auth)):
    return {"status": "ok", "db": "pending", "broker": "pending"}

@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.app_name}
