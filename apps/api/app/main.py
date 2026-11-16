"""Точка входу FastAPI-застосунку FactCheck."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

WEB_DIRECTORY = Path(__file__).resolve().parents[2] / "web"

app = FastAPI(
    title="FactCheck API",
    version="0.1.0",
    description="Наскрізний каркас системи перевірки новин.",
)
app.include_router(router)
app.mount("/", StaticFiles(directory=WEB_DIRECTORY, html=True), name="web")
