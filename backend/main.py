"""
Aadhaar Analytics Portal — Backend
FastAPI application entry point.
"""

import logging
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.routes import auth, live_stats, history, insights, anomalies, data_export, data_import, chat

app = FastAPI(
    title="Aadhaar Analytics Portal API",
    description="Backend API for analysing Aadhaar enrolment, demographic, and biometric data.",
    version="1.0.0",
)

logger = logging.getLogger("backend")

# -----------------------------------------------------------------
# CORS — only the origins listed in CORS_ORIGINS (comma-separated).
# The bundled frontend is served from the same origin and needs no CORS;
# list other origins only if a separately hosted frontend calls this API.
# -----------------------------------------------------------------
DEFAULT_CORS_ORIGINS = "http://localhost:8000,http://127.0.0.1:8000"
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,  # auth uses a Bearer header, not cookies
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


# -----------------------------------------------------------------
# Errors — unexpected exceptions become a JSON 500; the stack trace is
# logged on the server and never sent to the client.
# -----------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

from fastapi.responses import FileResponse

# -----------------------------------------------------------------
# Routers
# -----------------------------------------------------------------
app.include_router(auth.router,        prefix="/api/auth",      tags=["Authentication"])
app.include_router(live_stats.router,  prefix="/api/live",      tags=["Live Statistics"])
app.include_router(history.router,     prefix="/api/history",   tags=["Past History"])
app.include_router(insights.router,    prefix="/api/insights",  tags=["Insights"])
app.include_router(anomalies.router,   prefix="/api/anomalies", tags=["Anomalies"])
app.include_router(data_export.router, prefix="/api/export",    tags=["Data Export"])
app.include_router(data_import.router, prefix="/api/import",    tags=["Data Import & Predictive Analytics"])
app.include_router(chat.router,        prefix="/api/chat",      tags=["AI Chatbot"])

@app.get("/health", tags=["Health"])
def health():
    # Registered before the static mount at "/", which would otherwise
    # catch this path and return 404.
    return {"status": "ok", "message": "Aadhaar Analytics Portal API is running."}


# -----------------------------------------------------------------
# Frontend routes
# -----------------------------------------------------------------
@app.get("/", response_class=FileResponse)
async def serve_login():
    """Serve the login page as the root page."""
    return FileResponse(_frontend / "pages" / "login.html", media_type="text/html")

@app.get("/dashboard", response_class=FileResponse)
async def serve_dashboard():
    """Serve the dashboard page."""
    return FileResponse(_frontend / "pages" / "dashboard.html", media_type="text/html")

# -----------------------------------------------------------------
# Serve frontend static files
# -----------------------------------------------------------------
_frontend = Path(__file__).resolve().parent.parent / "frontend"
if _frontend.is_dir():
    app.mount("/css", StaticFiles(directory=str(_frontend / "css")), name="css")
    app.mount("/js",  StaticFiles(directory=str(_frontend / "js")),  name="js")
    app.mount("/",    StaticFiles(directory=str(_frontend / "pages"), html=True), name="pages")
