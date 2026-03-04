from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import auth, projects, dashboard, settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Real-time job cost management for telecom construction PMs",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under /api/v1
app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}
