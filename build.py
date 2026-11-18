#!/usr/bin/env python3
"""Gera o site estático da Casa Sem Apagão a partir de produtos.json.

Saída: produtos.js, index.html, calculadora/index.html, <id>/index.html (uma página por produto),
sitemap.xml e robots.txt.  Rode:  python3 build.py
"""
import json, html, os

BASE = "https://energia.ofertadorafa.com.br"
PIXEL = "2156050925299390"
ROOT = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(ROOT, "produtos.json"), encoding="utf-8"))
BY = {p["id"]: p for p in P}
CATS = [("estacao", "Estações de energia", "Silenciosas, sem gasolina, funcionam dentro de casa e ligam sozinhas na queda."),
        ("gerador", "Geradores a gasolina", "Mais potência por real, mas só do lado de fora de casa, com barulho e combustível."),
        ("protecao", "Proteção e itens de entrada", "Baratos e resolvem o susto: internet sem piscar, aparelho sem queimar, casa sem escuro.")]
CATNOME = {c: n for c, n, _ in CATS}

e = lambda s: html.escape(str(s), quote=True)
def brl(n): return f"{int(round(n)):,}".replace(",", ".")

ICON_EXT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>'
ICON_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
ICON_SHIELD = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>'
ICON_TRUCK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2M15 18H9M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.62l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/></svg>'
ICON_CARD = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="20" height="14" x="2" y="5" rx="2"/><path d="M2 10h20"/></svg>'
LOGO_SVG = '<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" fill="#16243A"/><path d="M12 30 32 13l20 17v21H12z" fill="none" stroke="#F5A524" stroke-width="4" stroke-linejoin="round"/><path d="M34 26l-8 12h6l-2 9 8-12h-6z" fill="#F5A524"/></svg>'


def specs(p):
    s = []
    if p.get("capacidadeWh"): s.append(f"{brl(p['capacidadeWh'])} Wh")
    if p.get("potenciaW"): s.append(f"{brl(p['potenciaW'])} W")
    return " · ".join(s) if s else CATNOME[p["categoria"]]


def ml(p, inner, cls="", origem=""):
    return (f'<a class="{cls}" href="{e(p["link"])}" target="_blank" rel="noopener sponsored" '
            f'data-ml="{p["id"]}" data-origem="{origem}">{inner}</a>')


def img(p, eager=False):
    return f'<img src="{e(p["imagem"])}" alt="{e(p["nome"])}" {"" if eager else "loading=\"lazy\" "}decoding="async">'


def head(title, desc, path, og_img, extra=""):
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{BASE}{path}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}{path}">
<meta property="og:site_name" content="Casa Sem Apagão">
<meta property="og:image" content="{e(og_img)}">
<meta name="theme-color" content="#0B1626">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://http2.mlstatic.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css?v=2">
<script>
!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init','{PIXEL}');fbq('track','PageView');
</script>
<noscript><img height="1" width="1" style="display:none" alt="" src="https://www.facebook.com/tr?id={PIXEL}&ev=PageView&noscript=1"></noscript>
{extra}</head>"""


def header(atual=""):
    cur = lambda k: ' aria-current="page"' if k == atual else ""
    return f"""<div class="topbar">Black Friday chegando: os preços de estação de energia costumam cair — confira hoje</div>
<header class="hdr"><div class="wrap">
  <a class="logo" href="/" aria-label="Casa Sem Apagão">{LOGO_SVG}<span>Casa Sem Apagão</span></a>
  <nav class="menu" aria-label="Menu">
    <a href="/#produtos"{cur('produtos')}>Produtos</a>
    <a class="calc-link" href="/calculadora/"{cur('calculadora')}>Calculadora</a>
    <a class="hide-sm" href="/#duvidas">Dúvidas</a>
  </nav>
</div></header>"""


def footer():
    return """<footer class="navy"><div class="in">
  <p>Casa Sem Apagão © 2026 · Indicamos produtos vendidos no Mercado Livre. Ao comprar pelos nossos links podemos receber uma comissão, sem custo extra pra você. Preços e estoque mudam todo dia; o valor final é o do Mercado Livre.</p>
  <a href="/#produtos">Produtos</a> · <a href="/calculadora/">Calculadora</a> · <a href="/privacidade.html">Política de privacidade</a>
</div></footer>"""


def scripts(extra=""):
    return f'<script src="/produtos.js?v=2"></script>\n<script src="/assets/app.js?v=3"></script>\n{extra}</body>\n</html>\n'


def card(p, origem="vitrine"):
    selo = f'<span class="selo">{e(p["selo"])}</span>' if p.get("selo") else ""
    pts = "".join(f"<li>{ICON_CHECK}<span>{e(t)}</span></li>" for t in p["pontos"])
    return f"""<article class="card">
  {ml(p, img(p) + selo, "foto", origem + "-foto")}
  <div class="corpo">
    <div><h3><a href="/{p['id']}/">{e(p['nome'])}</a></h3><p class="spec">{specs(p)} · {e(p['voltagem'])}</p></div>
    <ul class="checks">{pts}</ul>
    <p class="preco">por volta de <b>R$ {brl(p['precoAprox'])}</b></p>
    {ml(p, 'Comprar agora no Mercado Livre ' + ICON_EXT, "ml", origem + "-botao")}
    <a class="det" href="/{p['id']}/">Ver detalhes e quanto tempo segura →</a>
  </div>
</article>"""


# ---------------------------------------------------------------- produtos.js
with open(os.path.join(ROOT, "produtos.js"), "w", encoding="utf-8") as f:
    f.write("// GERADO por build.py a partir de produtos.json — edite o JSON e rode python3 build.py\n")
    f.write("window.PRODUTOS = " + json.dumps(P, ensure_ascii=False, indent=1) + ";\n")

# ---------------------------------------------------------------- index
secoes = ""
for c, nome, sub in CATS:
    cards = "\n".join(card(p, "home") for p in P if p["categoria"] == c)
    secoes += f'<h2 class="cat-title" id="{c}">{nome}</h2><p class="cat-sub">{sub}</p>\n<div class="grid">\n{cards}\n</div>\n'
    if c == "estacao":
        secoes += """<div class="calc-cta"><div><h3>Não sabe qual escolher?</h3><p>Marque o que você quer manter ligado e veja quanto tempo cada estação aguenta.</p></div>
<a class="btn btn-amber" href="/calculadora/">Abrir a calculadora</a></div>\n"""

COMP = [("Barulho", "Silenciosa", "Alto", "Silencioso"), ("Pode usar dentro de casa", "Sim", "Não", "Sim"),
        ("Liga sozinho na queda", "Sim (modo UPS)", "Não", "Sim"), ("Combustível", "Tomada ou sol", "Gasolina", "Tomada"),
        ("Autonomia", "Horas a dias", "Enquanto tiver gasolina", "Minutos"),
        ("Faixa de preço", "R$ 2.100–10.500", "R$ 1.500–4.000", "R$ 300–800")]
TIPOS = ["Estação de energia", "Gerador a gasolina", "Nobreak comum"]
tbl = ('<table><thead><tr><th></th>' + "".join(f'<th{" class=hl" if i == 0 else ""}>{t}</th>' for i, t in enumerate(TIPOS)) +
       '</tr></thead><tbody>' + "".join('<tr><th>' + r[0] + '</th>' + "".join(f'<td{" class=hl" if i == 0 else ""}>{v}</td>' for i, v in enumerate(r[1:])) + '</tr>' for r in COMP) + '</tbody></table>')
cmp = "".join(f'<div{" class=hl" if i == 0 else ""}><h3 style="font-size:17px">{t}</h3><dl>' + "".join(f'<div><dt>{r[0]}</dt><dd>{r[i+1]}</dd></div>' for r in COMP) + '</dl></div>' for i, t in enumerate(TIPOS))
FAQ = [("Quanto tempo uma estação segura a geladeira?", "Sozinha, uma geladeira comum gasta em média 60–80 W, então uma estação de 1 kWh segura cerca de 10 a 12 horas. Junto com Wi‑Fi, celulares e algumas luzes, conte com 6 a 8 horas. Uma de 2 kWh passa de um dia."),
       ("Liga ar-condicionado?", "Modelos de 1800 W ou mais ligam um split pequeno inverter por pouco tempo, mas esse não é o uso ideal. Elas brilham com internet, geladeira, luz e eletrônicos."),
       ("Precisa de instalação?", "Não. É só ligar a estação na tomada e plugar os aparelhos nela."),
       ("O que é modo nobreak/UPS?", "A estação fica ligada na tomada e, quando a luz cai, assume sozinha em milissegundos. Seus aparelhos nem percebem."),
       ("Dá pra carregar com placa solar?", "Sim, todas as estações listadas aceitam painel solar."),
       ("E a voltagem?", "Cada anúncio indica a versão (127V ou 220V). Confira a voltagem da sua tomada antes de comprar; em vários anúncios dá pra escolher a outra versão."),
       ("É seguro comprar pelo link?", "Sim. A compra é feita no próprio Mercado Livre, com Compra Garantida. Nós só indicamos os produtos.")]
faq = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in FAQ)
chips = "".join(f'<a class="chipa" href="#{c}">{n}</a>' for c, n, _ in CATS)

index = head("Casa Sem Apagão — energia de reserva para sua casa",
             "Faltou luz? Estações de energia silenciosas que ligam sozinhas na queda, geradores e proteção. As melhores opções do Mercado Livre.",
             "/", BY["ecoflow-delta3"]["imagem"]) + f"""
<body>
{header('produtos')}
<section class="navy hero"><div class="wrap">
  <h1>Faltou luz? <b>Sua casa continua funcionando.</b></h1>
  <p>Estações de energia que ligam sozinhas na queda: Wi‑Fi, geladeira, notebook e luz seguem funcionando. Sem gasolina, sem barulho.</p>
  <ul class="trust"><li>{ICON_SHIELD}Compra garantida pelo Mercado Livre</li><li>{ICON_TRUCK}Entrega rápida</li><li>{ICON_CARD}Parcelado no cartão</li></ul>
</div></section>
<main class="wrap" id="produtos" style="scroll-margin-top:70px">
  <nav class="chips" aria-label="Categorias">{chips}</nav>
  {secoes}
  <p class="disc">Preços e estoque mudam todo dia; o valor final é o do Mercado Livre.</p>
</main>
<section class="sec"><div class="wrap">
  <div class="sec-title"><h2>Estação, gerador ou nobreak?</h2></div>
  <div class="tbl">{tbl}</div><div class="cmp-cards">{cmp}</div>
</div></section>
<section class="sec alt" id="duvidas" style="scroll-margin-top:70px"><div class="wrap">
  <div class="sec-title"><h2>Perguntas frequentes</h2></div>
  <div class="faq">{faq}</div>
</div></section>
{footer()}
""" + scripts()
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(index)

# ---------------------------------------------------------------- calculadora
calc = head("Calculadora: quanto tempo minha casa aguenta sem luz? — Casa Sem Apagão",
            "Marque os aparelhos que você quer manter ligados e veja qual estação de energia aguenta e por quanto tempo.",
            "/calculadora/", BY["bluetti-ac180p"]["imagem"]) + f"""
<body>
{header('calculadora')}
<section class="sec" style="padding-top:28px"><div class="wrap">
  <div class="sec-title"><h2>Quanto tempo minha casa aguenta?</h2><p>Marque o que você quer manter ligado e veja qual estação cobre sua casa.</p></div>
  <div class="calc">
    <div class="panel">
      <h3>1. O que você quer manter ligado?</h3>
      <ul class="apar" id="aparelhos"></ul>
      <h3 style="margin-top:24px">2. Por quantas horas você quer aguentar?</h3>
      <div class="horas" role="radiogroup" id="horas"></div>
      <button class="ver" id="ver" type="button">⚡ Ver resultado</button>
    </div>
    <div id="resultado" hidden style="scroll-margin-top:70px"></div>
    <p style="text-align:center;margin-top:24px"><a href="/#produtos" style="font-weight:600">← Ver todos os produtos</a></p>
  </div>
</div></section>
{footer()}
""" + scripts('<script src="/assets/calculadora.js?v=2"></script>\n')
os.makedirs(os.path.join(ROOT, "calculadora"), exist_ok=True)
open(os.path.join(ROOT, "calculadora", "index.html"), "w", encoding="utf-8").write(calc)

# ---------------------------------------------------------------- páginas de produto
CARGAS = [("Só internet", "Roteador + modem", 20), ("Geladeira sozinha", "consumo médio", 70),
          ("Home office", "notebook + monitor + Wi‑Fi", 110), ("Casa no básico", "geladeira + Wi‑Fi + 3 luzes + 2 celulares", 147),
          ("Sala ligada", "TV + Wi‑Fi + ventilador + 2 luzes", 198)]


def horas_txt(h):
    if h >= 48: return f"~{round(h/24)} dias"
    if h >= 10: return f"~{round(h)} h"
    return f"~{h:.1f} h".replace(".", ",")


for p in P:
    pts = "".join(f"<li>{ICON_CHECK}<span>{e(t)}</span></li>" for t in p["pontos"])
    chips_p = [f"Versão {e(p['voltagem'])}"]
    if p.get("capacidadeWh"): chips_p.insert(0, f"{brl(p['capacidadeWh'])} Wh de bateria")
    if p.get("potenciaW"): chips_p.insert(1 if p.get("capacidadeWh") else 0, f"{brl(p['potenciaW'])} W (pico {brl(p['picoW'])} W)")
    chips_html = "".join(f"<li>{c}</li>" for c in chips_p)
    extra_bloco = ""
    if p["categoria"] == "estacao":
        linhas = "".join(f"<tr><td>{n}<small>{d} · {w} W</small></td><td>{horas_txt(p['capacidadeWh']*0.85/w)}</td></tr>" for n, d, w in CARGAS)
        extra_bloco = f"""<section class="sec alt"><div class="wrap" style="max-width:760px">
  <div class="sec-title" style="margin-bottom:18px"><h2>Quanto tempo a {e(p['nome'])} segura?</h2><p>Estimativa com {brl(p['capacidadeWh'])} Wh e 85% de aproveitamento da bateria.</p></div>
  <div class="aut"><table>{linhas}</table></div>
  <p class="nota" style="text-align:center">Liga aparelhos de até {brl(p['potenciaW'])} W ao mesmo tempo (pico de {brl(p['picoW'])} W na partida de motores, como o da geladeira).</p>
  <p style="text-align:center;margin-top:16px"><a class="btn btn-amber" href="/calculadora/">Calcular com os meus aparelhos</a></p>
</div></section>"""
    elif p["categoria"] == "gerador":
        extra_bloco = """<section class="sec alt"><div class="wrap" style="max-width:760px">
  <div class="aviso"><b>Importante:</b> gerador a gasolina só pode funcionar do lado de fora de casa, em lugar ventilado (a fumaça tem monóxido de carbono). Pra ter energia dentro de casa sem barulho, veja as <a href="/#estacao">estações de energia</a>.</div>
</div></section>"""
    rel = [q for q in P if q["categoria"] == p["categoria"] and q["id"] != p["id"]][:3]
    if len(rel) < 3: rel += [q for q in P if q["categoria"] == "estacao" and q["id"] != p["id"] and q not in rel][:3 - len(rel)]
    rel_html = "\n".join(card(q, "relacionados") for q in rel)
    desc = f"{p['nome']}: {p['resumo']}"
    page = head(f"{p['nome']} — Casa Sem Apagão", desc, f"/{p['id']}/", p["imagem"]) + f"""
<body data-produto="{p['id']}">
{header()}
<main class="wrap">
  <p class="crumb"><a href="/">Início</a> › <a href="/#{p['categoria']}">{CATNOME[p['categoria']]}</a></p>
  <div class="pp">
    {ml(p, img(p, eager=True) + (f'<span class="selo">{e(p["selo"])}</span>' if p.get('selo') else ''), "pp-foto", "produto-foto")}
    <div>
      <h1>{e(p['nome'])}</h1>
      <p class="resumo-txt">{e(p['resumo'])}</p>
      <ul class="chipset">{chips_html}</ul>
      <ul class="checks">{pts}</ul>
      <div class="preco-box" data-flut-alvo>
        <div class="valor">R$ {brl(p['precoAprox'])}</div>
        <small>preço de referência — o valor de hoje (e cupons) aparece no Mercado Livre</small>
        {ml(p, 'Comprar agora no Mercado Livre ' + ICON_EXT, "ml", "produto-botao")}
        <ul class="garantias"><li>{ICON_SHIELD}Compra Garantida: você recebe o produto ou o dinheiro de volta</li><li>{ICON_CARD}Parcelamento e frete calculados no Mercado Livre</li></ul>
      </div>
    </div>
  </div>
</main>
{extra_bloco}
<section class="sec"><div class="wrap">
  <h2 class="cat-title" style="margin-top:0">Compare com outras opções</h2><p class="cat-sub">Veja também:</p>
  <div class="grid">{rel_html}</div>
  <p style="text-align:center;margin-top:22px"><a href="/#produtos" style="font-weight:600">Ver todos os produtos →</a></p>
</div></section>
{footer()}
<div class="flut" id="flut" aria-hidden="true"><div class="fp">por volta de<b>R$ {brl(p['precoAprox'])}</b></div>{ml(p, 'Comprar agora ' + ICON_EXT, "ml", "produto-barra")}</div>
""" + scripts()
    os.makedirs(os.path.join(ROOT, p["id"]), exist_ok=True)
    open(os.path.join(ROOT, p["id"], "index.html"), "w", encoding="utf-8").write(page)

# ---------------------------------------------------------------- sitemap / robots
urls = ["/", "/calculadora/"] + [f"/{p['id']}/" for p in P]
open(os.path.join(ROOT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"  <url><loc>{BASE}{u}</loc></url>\n" for u in urls) + "</urlset>\n")
open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
print("ok:", len(P), "produtos;", len(urls), "páginas")
