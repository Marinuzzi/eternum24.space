# Eternum24 - Documentazione Sicurezza

## Architettura

```
┌─────────────────────────────────────────────────────────────────────┐
│                           UTENTE                                     │
│                              │                                       │
│                              ▼                                       │
│                    https://eternum24.space                          │
│                              │                                       │
├──────────────────────────────┼──────────────────────────────────────┤
│         VERCEL (CDN)         │         HETZNER (API)                │
│                              │                                       │
│  ┌─────────────────────┐     │     ┌─────────────────────┐         │
│  │    index.html       │     │     │   FastAPI :8003     │         │
│  │    textures/        │◄────┼────►│   /api/ping         │         │
│  │    (static files)   │     │     │   /api/audio/*      │         │
│  └─────────────────────┘     │     └─────────────────────┘         │
│                              │              │                        │
│                              │              ▼                        │
│                              │     ┌─────────────────────┐         │
│                              │     │  /var/www/html/     │         │
│                              │     │  eternum24/audio/   │         │
│                              │     │  (MP3 files)        │         │
│                              │     │  NON PUBBLICO       │         │
│                              │     └─────────────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Misure di Sicurezza Implementate

### 1. Kill Switch (Soft Block)

**Cosa fa:** Permette di disabilitare l'intero sito con una singola variabile.

**Come funziona:**
```python
# /var/www/html/eternum24/server/main.py
SITE_ENABLED = True  # Cambia a False per bloccare
```

**Comportamento:**
- `SITE_ENABLED = True` → `/api/ping` risponde `{"ok": true}` → sito funziona
- `SITE_ENABLED = False` → `/api/ping` risponde `{"ok": false}` → overlay di blocco

**Overlay di blocco mostra:**
- Messaggio "Servizio Sospeso"
- Email: johnfyrmell@gmail.com
- Link: https://formspree.io/f/myzkpzdv

**Come attivare/disattivare:**
```bash
ssh fra@167.235.23.19
sudo nano /var/www/html/eternum24/server/main.py
# Cambia SITE_ENABLED
sudo systemctl restart eternum24
```

---

### 2. Audio Non Pubblico

**Cosa fa:** I file MP3 non sono accessibili direttamente, solo tramite API.

**Implementazione:**

| Layer | Protezione |
|-------|------------|
| **Nginx** | `location /audio/ { return 404; }` - blocca accesso diretto |
| **FastAPI** | Solo endpoint `/api/audio/{file}` serve i file |
| **File system** | Audio in `/var/www/html/eternum24/audio/` (non in `public/`) |

**Nginx config (`/etc/nginx/sites-enabled/eternum24-api`):**
```nginx
location /audio/ {
    return 404;  # Blocca accesso diretto
}
```

---

### 3. Path Traversal Protection

**Cosa fa:** Impedisce attacchi tipo `../../../etc/passwd`

**Implementazione (`main.py`):**
```python
# Blocca caratteri pericolosi
if "/" in filename or "\\" in filename or ".." in filename:
    raise HTTPException(status_code=400, detail="Invalid filename")

# Verifica che il file sia dentro AUDIO_DIR
fpath = (AUDIO_DIR / filename).resolve()
try:
    fpath.relative_to(AUDIO_DIR.resolve())
except ValueError:
    raise HTTPException(status_code=400, detail="Invalid path")
```

---

### 4. Anti-Cache Headers

**Cosa fa:** Impedisce al browser di salvare i file audio in cache.

**Headers inviati:**
```python
headers = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
    "X-Robots-Tag": "noindex, nofollow",
}
```

**Benefici:**
- Browser non salva i file localmente
- File non indicizzati dai motori di ricerca
- Revoca futura possibile senza problemi di cache

---

### 5. CORS Controllato

**Cosa fa:** Permette solo domini autorizzati a chiamare l'API.

**Implementazione:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://eternum24.space",
        "https://www.eternum24.space",
        "http://localhost:3000",  # dev
    ],
    allow_methods=["GET"],  # Solo lettura
    allow_headers=["*"],
)
```

**Protezione:** Altri siti non possono chiamare l'API (il browser blocca).

---

### 6. File Type Validation

**Cosa fa:** Accetta solo file MP3.

```python
if not filename.endswith(".mp3"):
    raise HTTPException(status_code=400, detail="Only mp3 allowed")
```

---

### 7. Security Headers (Nginx)

```nginx
add_header X-Content-Type-Options nosniff always;
add_header X-Frame-Options SAMEORIGIN always;
add_header X-Robots-Tag "noindex, nofollow" always;
```

| Header | Protezione |
|--------|------------|
| `X-Content-Type-Options: nosniff` | Previene MIME sniffing |
| `X-Frame-Options: SAMEORIGIN` | Previene clickjacking |
| `X-Robots-Tag: noindex` | Non indicizzare l'API |

---

### 8. Separazione Frontend/Backend

| Componente | Hosting | Dominio |
|------------|---------|---------|
| Frontend (HTML/JS) | Vercel | eternum24.space |
| Backend (API) | Hetzner | api.eternum24.space |
| Audio (MP3) | Hetzner | (non pubblico) |

**Vantaggi:**
- Frontend su CDN veloce (Vercel)
- Audio protetto su server controllato (Hetzner)
- Kill switch indipendente dal frontend

---

### 9. MP3 Rimossi da Git/Vercel

**Stato:**
- ❌ GitHub: MP3 non tracciati (`.gitignore`)
- ❌ Vercel: MP3 non deployati
- ✅ Hetzner: MP3 serviti via API
- ✅ Locale: MP3 come backup

**`.gitignore`:**
```
*.mp3
```

---

### 10. ID3 Tags Puliti

**Prima:**
```
Artista: SUNO
URL: https://suno.com/...
```

**Dopo:**
```
Titolo: Franciscus de Caelo
Artista: John Fyrmell
Album: In Memoriam Papae Francisci
```

---

## Cosa NON è Implementato (e perché)

| Feature | Motivo |
|---------|--------|
| DRM | Overkill per questo progetto |
| HLS/DASH streaming | Complessità non necessaria |
| Token temporanei | Può essere aggiunto in futuro |
| Rate limiting | Può essere aggiunto con `slowapi` |
| Login/Auth | Non richiesto |
| Database | Non necessario per kill switch |
| Offuscamento URL | Attrito minimo, non sicurezza vera |

---

## Step Successivi (Opzionali)

### 1. Token Temporanei per Audio

**Complessità:** Media  
**Beneficio:** URL audio validi solo per X minuti

```python
import secrets
import time

tokens = {}  # {token: expiry_timestamp}

@app.get("/api/get-audio-token/{filename}")
def get_token(filename: str):
    token = secrets.token_urlsafe(32)
    tokens[token] = time.time() + 300  # 5 minuti
    return {"token": token}

@app.get("/api/audio/{token}/{filename}")
def audio_with_token(token: str, filename: str):
    if token not in tokens or tokens[token] < time.time():
        raise HTTPException(403, "Token expired")
    del tokens[token]  # Uso singolo
    # ... serve file
```

---

### 2. Rate Limiting

**Complessità:** Bassa  
**Beneficio:** Limita richieste per IP

```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/audio/{filename}")
@limiter.limit("10/minute")
def audio(filename: str):
    # ...
```

---

### 3. Logging/Analytics

**Complessità:** Bassa  
**Beneficio:** Traccia chi ascolta cosa

```python
import logging

logging.basicConfig(filename='/var/log/eternum24/access.log')

@app.get("/api/audio/{filename}")
def audio(filename: str, request: Request):
    logging.info(f"{request.client.host} - {filename}")
    # ...
```

---

### 4. Offuscamento Nomi File

**Complessità:** Bassa  
**Beneficio:** URL non indovinabili

```bash
# Rinomina
mv Franciscus-de-Caelo-IT.mp3 a8f3c2b1.mp3

# Mapping in main.py
FILE_MAP = {
    "IT": "a8f3c2b1.mp3",
    "FR": "b7e4d3c2.mp3",
    # ...
}
```

---

### 5. Watermarking Audio

**Complessità:** Alta  
**Beneficio:** Traccia chi ha distribuito un file leaked

Richiede:
- Generazione watermark unico per sessione
- FFmpeg per embedding
- Database per tracking

---

### 6. Backup Automatico

```bash
# Crontab
0 3 * * * tar -czf /backup/eternum24-$(date +%Y%m%d).tar.gz /var/www/html/eternum24/audio/
```

---

## Comandi Utili

### Monitoraggio

```bash
# Stato servizio
sudo systemctl status eternum24

# Log in tempo reale
sudo journalctl -u eternum24 -f

# Test API
curl https://api.eternum24.space/api/ping
```

### Kill Switch

```bash
# Blocca
ssh fra@167.235.23.19 "sudo sed -i 's/SITE_ENABLED = True/SITE_ENABLED = False/' /var/www/html/eternum24/server/main.py && sudo systemctl restart eternum24"

# Sblocca
ssh fra@167.235.23.19 "sudo sed -i 's/SITE_ENABLED = False/SITE_ENABLED = True/' /var/www/html/eternum24/server/main.py && sudo systemctl restart eternum24"
```

### Aggiornamento Audio

```bash
# Copia nuovo file
scp nuovo-file.mp3 fra@167.235.23.19:/var/www/html/eternum24/audio/

# Pulisci tag
ssh fra@167.235.23.19 "cd /var/www/html/eternum24/audio && id3v2 --delete-all nuovo-file.mp3 && id3v2 -t 'Franciscus de Caelo' -a 'John Fyrmell' -A 'In Memoriam Papae Francisci' nuovo-file.mp3"
```

---

## Contatti Emergenza

- **Email:** johnfyrmell@gmail.com
- **Form:** https://formspree.io/f/myzkpzdv
- **Server:** fra@167.235.23.19

---

*Documentazione aggiornata: Gennaio 2026*
