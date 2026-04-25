"""FastAPI application entrypoint for Provenance.

Mounts routes, serves the dashboard template, and configures CORS.
"""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router
from config import APP_TITLE, APP_VERSION, APP_DESCRIPTION

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all for demo purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    """Serve the minimal dashboard HTML page."""
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content="<h1>Provenance</h1><p>Dashboard template not found. "
                "Visit <a href='/docs'>/docs</a> for API documentation.</p>",
        status_code=200,
    )
