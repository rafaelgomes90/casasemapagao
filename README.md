# Casa Sem Apagão

Site estático de afiliado (Mercado Livre) — energia de reserva pra casa. No ar em https://energia.ofertadorafa.com.br

- `produtos.json`: catálogo (link de afiliado com etiqueta, preço, foto, textos). **Edite aqui** e rode `python3 build.py`.
- `build.py`: gera `index.html`, `calculadora/`, uma página por produto (`/<id>/`), `produtos.js`, `sitemap.xml`.
- `assets/`: CSS, pixel/cliques (`app.js`) e calculadora.
- A VPS puxa este repositório a cada 5 min (Caddy do painel achadinhos serve a pasta `/var/www/casasemapagao`).
