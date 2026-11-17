#!/usr/bin/env bash
# Casa Sem Apagão — publica o site no Caddy (Docker) do painel achadinhos, sem mudar o painel.
# Uso: curl -fsSL <url>/usar-caddy-docker.sh | sudo DOMINIO_SITE=energia.ofertadorafa.com.br bash
set -euo pipefail

SITE="${DOMINIO_SITE:?defina DOMINIO_SITE=seu.subdominio}"
PROJ="/home/rafael/achadinhos"
WWW="/var/www/casasemapagao"
REPO="https://github.com/rafaelgomes90/casasemapagao.git"
CADDYFILE="$PROJ/Caddyfile"
OVERRIDE="$PROJ/docker-compose.override.yml"
TS=$(date +%Y%m%d%H%M%S)

cd "$PROJ"
if docker compose version >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi

echo "==> Limpando o nginx da tentativa anterior"
rm -f /etc/nginx/sites-enabled/casasemapagao /etc/nginx/sites-available/casasemapagao
systemctl disable --now nginx >/dev/null 2>&1 || true

echo "==> Baixando/atualizando o site em $WWW"
command -v git >/dev/null || { apt-get update -qq; DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git >/dev/null; }
git config --global --get-all safe.directory 2>/dev/null | grep -qx "$WWW" || git config --global --add safe.directory "$WWW"
if [ -d "$WWW/.git" ]; then git -C "$WWW" pull -q; else rm -rf "$WWW"; git clone -q "$REPO" "$WWW"; fi
chmod -R a+rX "$WWW"
echo "*/5 * * * * root git -C $WWW pull -q >/dev/null 2>&1 && chmod -R a+rX $WWW" > /etc/cron.d/casasemapagao

echo "==> Backup da configuração atual"
[ -f "$CADDYFILE" ] && cp "$CADDYFILE" "$CADDYFILE.bak-$TS"
[ -f "$OVERRIDE" ] && cp "$OVERRIDE" "$OVERRIDE.bak-$TS"

echo "==> Escrevendo o Caddyfile (painel igual + site novo)"
cat > "$CADDYFILE" <<CADDY
# Painel achadinhos (mesmo comportamento de antes: reverse-proxy pro app)
{\$DOMINIO} {
	reverse_proxy app:8000
}

# Casa Sem Apagão (site estático, atualiza sozinho do GitHub)
$SITE {
	root * /srv/casasemapagao
	encode gzip
	@bloqueado path /.git* *.sh *.md
	respond @bloqueado 404
	@estaticos path *.svg *.webp *.png *.jpg *.css
	header @estaticos Cache-Control "public, max-age=604800"
	@paginas path / *.html *.js
	header @paginas Cache-Control "no-cache"
	file_server
}
CADDY

cat > "$OVERRIDE" <<YML
# Adicionado pela Casa Sem Apagão: o Caddy passa a ler o Caddyfile (painel + site).
services:
  caddy:
    command: caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - $WWW:/srv/casasemapagao:ro
YML
chown rafael:rafael "$CADDYFILE" "$OVERRIDE" 2>/dev/null || true

echo "==> Validando a configuração"
DOM=$(grep -E '^DOMINIO=' .env | head -1 | cut -d= -f2- | tr -d "\"' ")
docker run --rm -e DOMINIO="$DOM" -v "$CADDYFILE:/etc/caddy/Caddyfile:ro" caddy:2 caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null

desfazer() {
  echo "!! Algo deu errado — voltando a configuração anterior"
  rm -f "$OVERRIDE" "$CADDYFILE"
  [ -f "$OVERRIDE.bak-$TS" ] && mv "$OVERRIDE.bak-$TS" "$OVERRIDE"
  [ -f "$CADDYFILE.bak-$TS" ] && mv "$CADDYFILE.bak-$TS" "$CADDYFILE"
  $DC up -d caddy
  exit 1
}

echo "==> Recriando só o container do Caddy (o app/painel não é tocado)"
$DC up -d --no-deps caddy || desfazer
sleep 8

echo "==> Conferindo o painel ($DOM)"
P=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 20 --resolve "$DOM:443:127.0.0.1" "https://$DOM/" || echo 000)
echo "   painel respondeu HTTP $P"
[ "$P" = "000" ] && desfazer

echo "==> Conferindo o site ($SITE) — o certificado pode levar uns segundos"
S=000
for i in 1 2 3 4 5 6; do
  S=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 --resolve "$SITE:443:127.0.0.1" "https://$SITE/" || echo 000)
  [ "$S" = "200" ] && break; sleep 10
done
echo "   site respondeu HTTP $S"
if [ "$S" = "200" ]; then
  echo "Pronto: https://$SITE  (painel continua em https://$DOM)"
else
  echo "O painel está ok. O certificado do site ainda não saiu (DNS pode estar propagando)."
  echo "Ver o log:  sudo docker logs --tail 30 achadinhos-caddy-1"
fi
