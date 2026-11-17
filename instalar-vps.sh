#!/usr/bin/env bash
# Casa Sem Apagão — instala o site na VPS (Debian/Ubuntu) com nginx.
# Uso:
#   sem domínio (prévia na porta 8080):  curl -fsSL <url>/instalar-vps.sh | sudo bash
#   com domínio (HTTPS):                 curl -fsSL <url>/instalar-vps.sh | sudo DOMINIO=casasemapagao.com.br EMAIL=voce@email.com bash
# O site se atualiza sozinho a cada 5 min a partir do GitHub (git pull).
set -euo pipefail

REPO="https://github.com/rafaelgomes90/casasemapagao.git"
DIR="/var/www/casasemapagao"
DOMINIO="${DOMINIO:-}"
EMAIL="${EMAIL:-}"
CONF="/etc/nginx/sites-available/casasemapagao"

echo "==> Instalando nginx e git"
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nginx git >/dev/null

echo "==> Baixando o site"
if [ -d "$DIR/.git" ]; then git -C "$DIR" pull -q; else git clone -q "$REPO" "$DIR"; fi
chown -R www-data:www-data "$DIR"

if [ -n "$DOMINIO" ]; then
  LISTEN="listen 80; listen [::]:80;"
  NAME="server_name $DOMINIO www.$DOMINIO;"
else
  LISTEN="listen 8080; listen [::]:8080;"
  NAME="server_name _;"
fi

echo "==> Configurando nginx"
cat > "$CONF" <<NGINX
server {
  $LISTEN
  $NAME
  root $DIR;
  index index.html;
  location ~ /\.git { deny all; }
  location ~* \.(sh|md)$ { deny all; }
  location / { try_files \$uri \$uri/ =404; }
  location ~* \.(svg|webp|png|jpg|css)$ { expires 7d; add_header Cache-Control "public"; }
  location ~* \.(html|js)$ { add_header Cache-Control "no-cache"; }
  gzip on; gzip_types text/css application/javascript image/svg+xml;
}
NGINX
ln -sf "$CONF" /etc/nginx/sites-enabled/casasemapagao
nginx -t -q
systemctl enable --now nginx >/dev/null 2>&1 || true
systemctl reload nginx

if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  if [ -n "$DOMINIO" ]; then ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null; else ufw allow 8080/tcp >/dev/null; fi
fi

echo "==> Atualização automática (a cada 5 min)"
cat > /etc/cron.d/casasemapagao <<CRON
*/5 * * * * root git -C $DIR pull -q >/dev/null 2>&1
CRON

if [ -n "$DOMINIO" ]; then
  echo "==> Certificado HTTPS (Let's Encrypt)"
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq certbot python3-certbot-nginx >/dev/null
  if [ -n "$EMAIL" ]; then EM="-m $EMAIL"; else EM="--register-unsafely-without-email"; fi
  certbot --nginx -n --agree-tos $EM --redirect -d "$DOMINIO" -d "www.$DOMINIO" || \
    echo "!! O HTTPS falhou. Confira se o DNS de $DOMINIO aponta pra este IP e rode o comando de novo."
  echo "Pronto: https://$DOMINIO"
else
  IP=$(curl -fsS https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')
  echo "Pronto (prévia): http://$IP:8080"
fi
