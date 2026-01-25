"""
Eternum24 - Backend Minimale
============================
Endpoint:
  /api/ping         → kill switch
  /api/audio/{file} → serve audio (non pubblico)

Kill switch: cambia SITE_ENABLED = False per bloccare tutto

NOTA: Gira su porta 8003 (8000-8002 occupate da pigna)
Avvio: uvicorn main:app --host 127.0.0.1 --port 8003
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os

app = FastAPI()

# ============================================
# CONFIGURAZIONE
# ============================================
SITE_ENABLED = True  # False = sito bloccato
AUDIO_DIR = Path(os.environ.get("AUDIO_DIR", "/var/www/html/eternum24/audio"))

# CORS per permettere chiamate da Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://eternum24.space",
        "https://www.eternum24.space",
        "http://localhost:3000",  # dev
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ============================================
# /api/ping - Kill Switch
# ============================================
@app.get("/api/ping")
def ping():
    """
    Client chiama questo all'avvio.
    Se ok=false → overlay di blocco.
    """
    return {"ok": bool(SITE_ENABLED)}

# ============================================
# /api/audio/{filename} - Serve MP3
# ============================================
@app.get("/api/audio/{filename}")
def audio(filename: str):
    """
    Serve file audio.
    - Solo se sito abilitato
    - Blocca path traversal
    - No cache, no index
    """
    # Kill switch attivo anche per audio
    if not SITE_ENABLED:
        return JSONResponse({"ok": False}, status_code=403)

    # Blocca path traversal (../ o simili)
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Solo mp3
    if not filename.endswith(".mp3"):
        raise HTTPException(status_code=400, detail="Only mp3 allowed")

    fpath = (AUDIO_DIR / filename).resolve()

    # Verifica che il file esista
    if not fpath.exists() or not fpath.is_file():
        raise HTTPException(status_code=404, detail="Not found")

    # Extra sicurezza: assicurati che stia dentro AUDIO_DIR
    try:
        fpath.relative_to(AUDIO_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")

    # Headers anti-cache e anti-index
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
        "X-Robots-Tag": "noindex, nofollow",
    }

    # FileResponse gestisce automaticamente Range requests per seek/streaming
    return FileResponse(
        path=str(fpath),
        media_type="audio/mpeg",
        headers=headers
    )

# ============================================
# /api/ - Info
# ============================================
@app.get("/api/")
def root():
    return {"service": "eternum24", "status": "ok" if SITE_ENABLED else "suspended"}
