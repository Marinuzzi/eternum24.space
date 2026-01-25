# Eternum24 - Backend Minimale

## Struttura sul Server

```
/var/www/eternum24/
├── public/              ← Nginx serve questi (index.html, textures/)
│   ├── index.html
│   └── textures/
├── audio/               ← NON pubblico! Solo via /api/audio/
│   ├── Franciscus-de-Caelo-IT.mp3
│   └── ...
└── server/              ← FastAPI backend
    ├── main.py
    ├── requirements.txt
    └── nginx.conf
```

## Flusso

```
Browser → eternum24.space/
         ├── /           → Nginx serve index.html
         ├── /textures/  → Nginx serve immagini
         └── /api/*      → Nginx proxy → FastAPI:8000
                              ├── /api/ping   → kill switch
                              └── /api/audio/ → serve MP3
```

## Deploy Rapido

### 1. Copia file sul server

```bash
# Dal tuo Mac
ssh fra@167.235.23.19 "mkdir -p /var/www/eternum24/{public,audio,server}"

# File pubblici
scp index.html fra@167.235.23.19:/var/www/eternum24/public/
scp -r textures fra@167.235.23.19:/var/www/eternum24/public/

# Audio (NON pubblico)
scp *.mp3 fra@167.235.23.19:/var/www/eternum24/audio/

# Backend
scp -r server/* fra@167.235.23.19:/var/www/eternum24/server/
```

### 2. Setup sul server

```bash
ssh fra@167.235.23.19
cd /var/www/eternum24/server
chmod +x deploy.sh
./deploy.sh
```

### 3. Configura Nginx

```bash
sudo cp nginx.conf /etc/nginx/sites-available/eternum24
sudo ln -sf /etc/nginx/sites-available/eternum24 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. HTTPS

```bash
sudo certbot --nginx -d eternum24.space -d www.eternum24.space
```

### 5. Attiva backend nel client

In `/var/www/eternum24/public/index.html`, cambia:

```javascript
const API_BASE = '';      // ← prima (file locali)
const API_BASE = '/api';  // ← dopo (backend attivo)
```

### 6. Test

```bash
# Sul server
curl http://localhost:8000/api/ping
# → {"ok":true}

# Da browser
https://eternum24.space/api/ping
```

## Kill Switch

### Bloccare il sito

```bash
ssh fra@167.235.23.19
sudo nano /var/www/eternum24/server/main.py
# Cambia: SITE_ENABLED = False
sudo systemctl restart eternum24
```

### Riattivare

```bash
# Cambia: SITE_ENABLED = True
sudo systemctl restart eternum24
```

## Comandi Utili

```bash
# Stato servizio
sudo systemctl status eternum24

# Log in tempo reale
sudo journalctl -u eternum24 -f

# Riavvia
sudo systemctl restart eternum24

# Test ping
curl -s http://localhost:8000/api/ping | jq

# Test audio (primi byte)
curl -I http://localhost:8000/api/audio/Franciscus-de-Caelo-IT.mp3
```

## Sicurezza

- **Audio non indicizzato**: header `X-Robots-Tag: noindex`
- **No cache**: browser non salva i file
- **Path traversal bloccato**: `../` non funziona
- **Nginx non serve /audio/**: solo FastAPI può farlo
- **Kill switch**: blocca tutto con una variabile

## Estensioni Future

Il codice è pronto per:

- **Token temporanei**: aggiungi validazione in `/api/audio`
- **Rate limiting**: usa `slowapi`
- **Logging**: logga richieste per analytics
- **Nomi file offuscati**: rinomina mp3 in hash
