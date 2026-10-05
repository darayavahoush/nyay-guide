import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .india_api import router as india_router
from .india import slm

app = FastAPI(title="Nyay Guide: India family-law agent")
origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])
app.include_router(india_router)


@app.on_event("startup")
def _load_slm():
    slm.start()          # background thread: the port binds at once, the encoder loads behind it


@app.get("/api/health")
def health():
    """Always ok=true so Render's health check passes while the encoder loads. Shows which engine is live and the peak memory."""
    return {"ok": True, "slm": slm.status(), "peak_rss_mb": slm.rss_mb()}


# Production: serve the built React app from the same origin (no CORS, one service).
DIST = Path(os.environ.get("FRONTEND_DIST", Path(__file__).resolve().parents[2] / "frontend" / "dist"))
if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = (DIST / path).resolve()
        if path and f.is_file() and DIST.resolve() in f.parents:
            return FileResponse(f)
        return FileResponse(DIST / "index.html")
