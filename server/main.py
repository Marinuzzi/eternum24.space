"""
Eternum24 - Backend Minimale
============================
Funzioni:
  1. /ping         → health check / kill switch
  2. /audio/{file} → serve file audio (non indicizzato)

Per attivare/disattivare il sito:
  - Cambia SITE_ENABLED = True/False
  - Oppure in futuro: leggi da file/db/env

Avvio:
  pip install fastapi uvicorn
  uvicorn main:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# ============================================
# CONFIGURAZIONE - Kill Switch
# ============================================
SITE_ENABLED = True  # Cambia a False per bloccare il sito

# Percorso dove stanno i file audio sul server
AUDIO_DIR = os.environ.get("AUDIO_DIR", "/var/www/eternum24/audio")

# Domini autorizzati (CORS)
ALLOWED_ORIGINS = [
    "https://eternum24.space",
    "https://www.eternum24.space",
    "http://localhost:3000",  # dev
    "http://127.0.0.1:5500",  # live server
]

# ============================================
# CORS - permette al frontend di chiamare il backend
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ============================================
# ENDPOINT: /ping - Health check / Kill switch
# ============================================
@app.get("/ping")
def ping():
    """
    Il client chiama questo endpoint all'avvio.
    Se ok=false, mostra overlay di blocco.
    
    Estendibile: in futuro puoi aggiungere:
      - check su database
      - verifica licenza
      - messaggi personalizzati
    """
    if SITE_ENABLED:
        return {"ok": True}
    else:
        return JSONResponse(
            status_code=200,  # 200 così il client riceve il JSON
            content={
                "ok": False,
                "message": "Sito temporaneamente sospeso",
                "contact": "johnfyrmell@gmail.com"
            }
        )

# ============================================
# ENDPOINT: /audio/{filename} - Serve file audio
# ============================================
@app.get("/audio/{filename}")
def get_audio(filename: str):
    """
    Serve i file audio.
    Non sono indicizzati pubblicamente.
    
    Sicurezza minima:
      - Verifica che il file esista
      - Previene path traversal (../)
      - In futuro: aggiungi token temporanei
    """
    # Previeni path traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Verifica estensione
    if not filename.endswith(".mp3"):
        raise HTTPException(status_code=400, detail="Only mp3 allowed")
    
    filepath = os.path.join(AUDIO_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        filepath,
        media_type="audio/mpeg",
        # No cache per poter revocare in futuro
        headers={"Cache-Control": "no-store, max-age=0"}
    )

# ============================================
# ENDPOINT: / - Info
# ============================================
@app.get("/")
def root():
    return {"service": "eternum24", "version": "1.0"}
