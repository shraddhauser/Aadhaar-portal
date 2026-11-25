"""
Aadhaar Analytics Portal — Backend
FastAPI application entry point.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routes import auth, live_stats, history, insights, anomalies, data_export, data_import, chat

app = FastAPI(
    title="Aadhaar Analytics Portal API",
    description="Backend API for analysing Aadhaar enrolment, demographic, and biometric data.",
    version="1.0.0",
)

# -----------------------------------------------------------------
# CORS — allow frontend origin (adjust in production)
# -----------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/health", tags=["Health"])
def root():
    return {"status": "ok", "message": "Aadhaar Analytics Portal API is running."}

