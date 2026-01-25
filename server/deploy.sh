#!/bin/bash
# ============================================
# Deploy Eternum24 su Hetzner
# ============================================
# SICURO: non tocca servizi esistenti (pigna, etc.)
# USA PORTA 8003 (8000-8002 già occupate)
# Esegui come: bash deploy.sh

set -e  # Esce se un comando fallisce

echo "=== Eternum24 Backend Setup ==="
echo ""
echo "NOTA: Questo script crea UN NUOVO servizio (eternum24)"
echo "      Non modifica: pigna-backend, pigna-flow, pigna-staging"
echo "      Usa porta: 8003"
echo ""

# 1. Crea struttura directory
echo "[1/6] Creazione directory..."
sudo mkdir -p /var/www/eternum24/public
sudo mkdir -p /var/www/eternum24/audio
sudo mkdir -p /var/www/eternum24/server

# 2. Copia file (se non già fatto)
echo "[2/6] Verifica file..."
if [ ! -f "/var/www/eternum24/server/main.py" ]; then
    echo "  → Copia i file con: scp -r server/* fra@server:/var/www/eternum24/server/"
fi

# 3. Installa dipendenze
echo "[3/6] Installazione dipendenze Python..."
cd /var/www/eternum24/server
pip3 install --user -r requirements.txt 2>/dev/null || pip3 install -r requirements.txt

# 4. Crea servizio systemd
echo "[4/6] Configurazione servizio systemd..."
sudo tee /etc/systemd/system/eternum24.service > /dev/null <<EOF
[Unit]
Description=Eternum24 API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/var/www/eternum24/server
Environment="AUDIO_DIR=/var/www/eternum24/audio"
ExecStart=$(which uvicorn || echo "/usr/local/bin/uvicorn") main:app --host 127.0.0.1 --port 8003
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 5. Abilita e avvia servizio
echo "[5/6] Avvio servizio..."
sudo systemctl daemon-reload
sudo systemctl enable eternum24
sudo systemctl restart eternum24

# 6. Configura Nginx (se non già fatto)
echo "[6/6] Nginx..."
if [ ! -f "/etc/nginx/sites-available/eternum24" ]; then
    echo "  → Copia nginx.conf:"
    echo "    sudo cp nginx.conf /etc/nginx/sites-available/eternum24"
    echo "    sudo ln -sf /etc/nginx/sites-available/eternum24 /etc/nginx/sites-enabled/"
    echo "    sudo nginx -t && sudo systemctl reload nginx"
    echo "    sudo certbot --nginx -d eternum24.space -d www.eternum24.space"
else
    echo "  → Nginx già configurato"
fi

echo ""
echo "=== Setup completato ==="
echo ""
echo "Struttura:"
echo "  /var/www/eternum24/"
echo "  ├── public/      ← index.html, textures/ (Nginx serve questi)"
echo "  ├── audio/       ← MP3 (NON pubblico, solo via API)"
echo "  └── server/      ← FastAPI (porta 8003)"
echo ""
echo "Prossimi passi:"
echo "  1. Copia index.html e textures/ in /var/www/eternum24/public/"
echo "  2. Copia *.mp3 in /var/www/eternum24/audio/"
echo "  3. Configura Nginx (AGGIUNGI site, non sostituire!)"
echo "  4. In index.html cambia: API_BASE = '/api'"
echo "  5. Test: curl http://localhost:8003/api/ping"
echo ""
echo "⚠️  ATTENZIONE: Nginx va configurato AGGIUNGENDO un site,"
echo "    non modificando quelli esistenti (pigna, flow, etc.)"
echo ""
echo "Kill switch: modifica SITE_ENABLED in main.py e riavvia"
echo "  sudo systemctl restart eternum24"
