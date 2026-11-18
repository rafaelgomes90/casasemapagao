#!/usr/bin/env bash
# Casa Sem Apagão — liga o contador de visitantes e o painel (/painel/) no Caddy (Docker) do painel achadinhos.
# Uso: curl -fsSL https://raw.githubusercontent.com/rafaelgomes90/casasemapagao/main/usar-painel.sh | sudo bash
set -euo pipefail

SITE="${DOMINIO_SITE:-energia.ofertadorafa.com.br}"
PROJ="/home/rafael/achadinhos"
WWW="/var/www/casasemapagao"
CADDYFILE="$PROJ/Caddyfile"
OVERRIDE="$PROJ/docker-compose.override.yml"
KEYFILE="$PROJ/.painel_key"
TS=$(date +%Y%m%d%H%M%S)

cd "$PROJ"
if docker compose version >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi

echo "==> Atualizando o site"
git -C "$WWW" pull -q && chmod -R a+rX "$WWW"
[ -f "$WWW/painel/server.py" ] || { echo "!! Não achei $WWW/painel/server.py"; exit 1; }

echo "==> Chave do painel"
[ -s "$KEYFILE" ] || head -c 18 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 20 > "$KEYFILE"
chmod 600 "$KEYFILE"; KEY=$(cat "$KEYFILE")
mkdir -p "$PROJ/visitas-data"

echo "==> Backup"
cp "$CADDYFILE" "$CADDYFILE.bak-$TS"
[ -f "$OVERRIDE" ] && cp "$OVERRIDE" "$OVERRIDE.bak-$TS"

echo "==> Caddy: /api/* do site vai pro contador"
if ! grep -q "reverse_proxy /api/\* visitas:8787" "$CADDYFILE"; then
  # edita no lugar (mesmo arquivo), pra o container do Caddy enxergar a mudança
  sed "s#^\(\s*\)root \* /srv/casasemapagao#&\n\1reverse_proxy /api/* visitas:8787#" "$CADDYFILE" > "$CADDYFILE.novo"
  cat "$CADDYFILE.novo" > "$CADDYFILE"; rm -f "$CADDYFILE.novo"
fi
grep -q "reverse_proxy /api/\* visitas:8787" "$CADDYFILE" || { echo "!! Não consegui editar o Caddyfile"; exit 1; }

echo "==> docker-compose.override.yml (Caddy + contador)"
cat > "$OVERRIDE" <<YML
# Casa Sem Apagão: o Caddy lê o Caddyfile (painel + site) e o contador de visitantes roda ao lado.
services:
  caddy:
    command: caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - $WWW:/srv/casasemapagao:ro
  visitas:
    image: python:3.12-alpine
    restart: unless-stopped
    command: python -u /app/server.py
    environment:
      - PAINEL_KEY=$KEY
      - DB=/data/visitas.db
      - TZ=America/Fortaleza
    volumes:
      - $WWW/painel:/app:ro
      - ./visitas-data:/data
YML
chown rafael:rafael "$CADDYFILE" "$OVERRIDE" 2>/dev/null || true

desfazer() {
  echo "!! Algo deu errado — voltando a configuração anterior"
  cat "$CADDYFILE.bak-$TS" > "$CADDYFILE"
  if [ -f "$OVERRIDE.bak-$TS" ]; then cat "$OVERRIDE.bak-$TS" > "$OVERRIDE"; else rm -f "$OVERRIDE"; fi
  docker rm -f achadinhos-visitas-1 >/dev/null 2>&1 || true
  $DC exec -T caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null 2>&1 || $DC restart caddy
  exit 1
}

echo "==> Validando o Caddyfile"
DOM=$(grep -E '^DOMINIO=' .env | head -1 | cut -d= -f2- | tr -d "\"' ")
docker run --rm -e DOMINIO="$DOM" -v "$CADDYFILE:/etc/caddy/Caddyfile:ro" caddy:2 caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null || desfazer

echo "==> Subindo o contador e recarregando o Caddy (o app do painel achadinhos não é tocado)"
docker rm -f achadinhos-visitas-1 >/dev/null 2>&1 || true
$DC up -d --no-deps visitas caddy || desfazer
sleep 3
echo "==> Recarregando a configuração do Caddy (sem derrubar nada)"
if $DC exec -T caddy grep -q "visitas:8787" /etc/caddy/Caddyfile 2>/dev/null; then
  $DC exec -T caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile || $DC restart caddy
else
  echo "   o Caddy está com o arquivo antigo preso; reiniciando ele (uns 3 segundos)"; $DC restart caddy
fi
sleep 4

echo "==> Conferindo"
P=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 --resolve "$DOM:443:127.0.0.1" "https://$DOM/" || echo 000)
A=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 --resolve "$SITE:443:127.0.0.1" "https://$SITE/api/painel?k=$KEY" || echo 000)
echo "   painel achadinhos: HTTP $P · contador: HTTP $A"
[ "$P" = "000" ] && desfazer
[ "$A" = "200" ] || { echo "   log do contador:"; $DC logs --tail 20 visitas; desfazer; }

echo
echo "Pronto! Abra o painel (guarde esse link, ele tem a chave):"
echo "   https://$SITE/painel/#k=$KEY"
