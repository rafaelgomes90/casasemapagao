#!/usr/bin/env bash
# Casa Sem Apagão — publica o site no Caddy que já roda na VPS (HTTPS automático).
# Uso: curl -fsSL <url>/usar-caddy.sh | sudo DOMINIO=energia.ofertadorafa.com.br bash
set -euo pipefail

REPO="https://github.com/rafaelgomes90/casasemapagao.git"
DIR="/var/www/casasemapagao"
DOMINIO="${DOMINIO:?defina DOMINIO=seu.subdominio}"
CADDYFILE="/etc/caddy/Caddyfile"

echo "==> Conferindo o Caddy"
if ! systemctl is-active --quiet caddy; then
  echo "!! O Caddy não está rodando como serviço do sistema (systemctl). Me mande a saída de:"
  echo "   sudo ss -ltnp | grep -E ':80|:443' ; docker ps 2>/dev/null"
  exit 1
fi
[ -f "$CADDYFILE" ] || { echo "!! Não achei $CADDYFILE"; exit 1; }

echo "==> Tirando o nginx do caminho (o Caddy já cuida das portas 80/443)"
rm -f /etc/nginx/sites-enabled/casasemapagao
systemctl disable --now nginx >/dev/null 2>&1 || true

echo "==> Baixando/atualizando o site"
command -v git >/dev/null || { apt-get update -qq; DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git >/dev/null; }
git config --global --get-all safe.directory 2>/dev/null | grep -qx "$DIR" || git config --global --add safe.directory "$DIR"
if [ -d "$DIR/.git" ]; then git -C "$DIR" pull -q; else git clone -q "$REPO" "$DIR"; fi
chmod -R a+rX "$DIR"

echo "==> Configurando $DOMINIO no Caddy"
cp "$CADDYFILE" "$CADDYFILE.bak-$(date +%Y%m%d%H%M%S)"
if ! grep -q "^$DOMINIO" "$CADDYFILE"; then
  cat >> "$CADDYFILE" <<CADDY

$DOMINIO {
	root * $DIR
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
fi
caddy validate --config "$CADDYFILE" --adapter caddyfile >/dev/null
systemctl reload caddy

echo "==> Atualização automática (a cada 5 min)"
echo "*/5 * * * * root git -C $DIR pull -q >/dev/null 2>&1 && chmod -R a+rX $DIR" > /etc/cron.d/casasemapagao

echo "Pronto: https://$DOMINIO (o certificado sai em alguns segundos)"
