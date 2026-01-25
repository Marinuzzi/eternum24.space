# Eternum24 - Backend Minimale

## Struttura

```
server/
├── main.py           # FastAPI backend
├── requirements.txt  # Dipendenze Python
├── deploy.sh        # Script di deploy
└── README.md        # Questo file
```

## Come funziona

### Kill Switch

1. Il client chiama `/ping` all'avvio
2. Se `SITE_ENABLED = True` → risponde `{ok: true}` → sito funziona
3. Se `SITE_ENABLED = False` → risponde `{ok: false}` → overlay di blocco

### Audio Protetto

- I file MP3 sono serviti da `/audio/{filename}`
- Non sono indicizzati pubblicamente
- URL non indovinabili senza conoscere i nomi

## Deploy su Hetzner

### 1. Copia i file sul server

```bash
# Dal tuo Mac
scp -r server/ fra@167.235.23.19:/var/www/eternum24/

# Copia anche i file MP3
scp *.mp3 fra@167.235.23.19:/var/www/eternum24/audio/
```

### 2. Installa e avvia

```bash
ssh fra@167.235.23.19
cd /var/www/eternum24/server
chmod +x deploy.sh
./deploy.sh
```

### 3. Configura Nginx

Aggiungi al tuo nginx config:

```nginx
server {
    server_name api.eternum24.space;  # o eternum24.space/api
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Poi: `sudo nginx -t && sudo systemctl reload nginx`

### 4. Attiva HTTPS

```bash
sudo certbot --nginx -d api.eternum24.space
```

### 5. Aggiorna il client

In `index.html`, cambia:

```javascript
const API_BASE = '';  // File locali
```

in:

```javascript
const API_BASE = 'https://api.eternum24.space';  // Backend attivo
```

## Comandi utili

```bash
# Stato del servizio
sudo systemctl status eternum24

# Log
sudo journalctl -u eternum24 -f

# Riavvia
sudo systemctl restart eternum24

# Test locale
curl http://localhost:8000/ping
```

## Kill Switch

Per **bloccare** il sito:

1. Modifica `main.py`:
   ```python
   SITE_ENABLED = False
   ```

2. Riavvia:
   ```bash
   sudo systemctl restart eternum24
   ```

Per **riattivare**: cambia a `True` e riavvia.

## Estensioni Future

Il codice è predisposto per:

- **Token temporanei**: aggiungi validazione in `/audio`
- **Database licenze**: aggiungi check in `/ping`
- **Rate limiting**: usa `slowapi` o middleware
- **Analytics**: logga le chiamate
