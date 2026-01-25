#!/bin/bash
# ============================================
# Deploy script per Hetzner
# ============================================
# Uso: scp -r server/ fra@167.235.23.19:/var/www/eternum24/
#      ssh fra@167.235.23.19 "cd /var/www/eternum24/server && bash deploy.sh"

echo "=== Eternum24 Backend Setup ==="

# 1. Crea directory audio se non esiste
mkdir -p /var/www/eternum24/audio

# 2. Installa dipendenze Python
pip3 install -r requirements.txt

# 3. Crea servizio systemd
sudo tee /etc/systemd/system/eternum24.service > /dev/null <<EOF
[Unit]
Description=Eternum24 API
After=network.target

[Service]
Type=simple
User=fra
WorkingDirectory=/var/www/eternum24/server
Environment="AUDIO_DIR=/var/www/eternum24/audio"
ExecStart=/usr/local/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 4. Abilita e avvia
sudo systemctl daemon-reload
sudo systemctl enable eternum24
sudo systemctl start eternum24

echo ""
echo "=== Setup completato ==="
echo "Backend in esecuzione su http://127.0.0.1:8000"
echo ""
echo "Prossimi passi:"
echo "1. Configura nginx per proxy /api → localhost:8000"
echo "2. Copia i file MP3 in /var/www/eternum24/audio/"
echo "3. Testa: curl http://localhost:8000/ping"
