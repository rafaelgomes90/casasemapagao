"""Casa Sem Apagão — contador de visitantes (só biblioteca padrão do Python).
Recebe os eventos do site em POST /api/hit e serve os dados do painel em GET /api/painel?k=CHAVE.
Guarda só cidade/UF aproximada (pelo IP), aparelho, página, produto e anúncio de origem. O IP não é gravado."""
import json, os, sys, sqlite3, threading, time, urllib.request, hashlib, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get('PORT', 8787))
KEY = os.environ.get('PAINEL_KEY', '')
DB = os.environ.get('DB', '/data/visitas.db')
TZ_OFFSET = -3 * 3600  # Fortaleza
ONLINE_S = 60

lock = threading.Lock()
con = sqlite3.connect(DB, check_same_thread=False)
con.execute('''CREATE TABLE IF NOT EXISTS ev(
  ts REAL, sid TEXT, tipo TEXT, pagina TEXT, produto TEXT, cidade TEXT, uf TEXT,
  aparelho TEXT, origem TEXT, anuncio TEXT)''')
con.execute('CREATE INDEX IF NOT EXISTS ev_ts ON ev(ts)')
if 'via' not in [r[1] for r in con.execute('PRAGMA table_info(ev)')]:
    con.execute("ALTER TABLE ev ADD COLUMN via TEXT DEFAULT ''")
con.execute('CREATE TABLE IF NOT EXISTS sess(sid TEXT PRIMARY KEY, ultimo REAL, pagina TEXT, cidade TEXT, uf TEXT, aparelho TEXT, anuncio TEXT)')
con.execute('CREATE TABLE IF NOT EXISTS ign(h TEXT PRIMARY KEY, ts REAL)')
con.commit()
IGN = {r[0] for r in con.execute('SELECT h FROM ign')}


def iphash(ip):
    return hashlib.sha256(('csa:' + ip).encode()).hexdigest()[:20]


def ip_de(req):
    return (req.headers.get('X-Forwarded-For') or req.client_address[0]).split(',')[0].strip()

_geo = {}  # cache em memória: hash do IP -> (cidade, uf)


def geo(ip):
    h = hashlib.sha256(ip.encode()).hexdigest()[:16]
    if h in _geo:
        return _geo[h]
    cid, uf = '', ''
    if ip and not ip.startswith(('10.', '172.', '192.168.', '127.')):
        try:
            with urllib.request.urlopen(f'http://ip-api.com/json/{ip}?fields=status,city,region&lang=pt-BR', timeout=3) as r:
                d = json.load(r)
            if d.get('status') == 'success':
                cid, uf = d.get('city', ''), d.get('region', '')
        except Exception:
            pass
    _geo[h] = (cid, uf)
    if len(_geo) > 20000:
        _geo.clear()
    return cid, uf


def aparelho(ua):
    ua = ua or ''
    if 'iPhone' in ua: return 'iPhone'
    if 'iPad' in ua: return 'iPad'
    if 'Android' in ua: return 'Android'
    if 'Windows' in ua: return 'Windows'
    if 'Mac OS' in ua: return 'Mac'
    return 'Outro'


def clip(s, n=120):
    return re.sub(r'[\x00-\x1f]', '', str(s or ''))[:n]


def inicio_do_dia():
    agora = time.time()
    return agora - ((agora + TZ_OFFSET) % 86400)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        if not self.path.startswith('/api/hit'):
            return self._json(404, {})
        try:
            n = min(int(self.headers.get('Content-Length', 0)), 4000)
            d = json.loads(self.rfile.read(n) or b'{}')
        except Exception:
            return self._json(400, {})
        tipo = d.get('t')
        if tipo not in ('view', 'ping', 'click'):
            return self._json(400, {})
        sid = clip(d.get('sid'), 40)
        if not sid:
            return self._json(400, {})
        ip = ip_de(self)
        if iphash(ip) in IGN or d.get('eu'):
            self.send_response(204); self.end_headers(); return
        now = time.time()
        with lock:
            row = con.execute('SELECT cidade, uf FROM sess WHERE sid=?', (sid,)).fetchone()
        cid, uf = row if row else geo(ip)
        ap = aparelho(self.headers.get('User-Agent'))
        pag, prod = clip(d.get('p')), clip(d.get('prod'), 60)
        origem, anuncio = clip(d.get('src'), 40), clip(d.get('ad'), 80)
        via = clip(d.get('via'), 12)
        with lock:
            con.execute('INSERT INTO sess VALUES(?,?,?,?,?,?,?) ON CONFLICT(sid) DO UPDATE SET ultimo=excluded.ultimo, pagina=excluded.pagina',
                        (sid, now, pag, cid, uf, ap, anuncio))
            if tipo != 'ping':
                con.execute('INSERT INTO ev(ts,sid,tipo,pagina,produto,cidade,uf,aparelho,origem,anuncio,via) VALUES(?,?,?,?,?,?,?,?,?,?,?)', (now, sid, tipo, pag, prod, cid, uf, ap, origem, anuncio, via))
            con.commit()
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if not self.path.startswith('/api/painel'):
            return self._json(404, {})
        from urllib.parse import urlparse, parse_qs
        k = parse_qs(urlparse(self.path).query).get('k', [''])[0]
        if not KEY or k != KEY:
            return self._json(403, {'erro': 'chave inválida'})
        now, hoje = time.time(), inicio_do_dia()
        h = iphash(ip_de(self))  # quem abre o painel (com a chave) deixa de ser contado nesse IP
        with lock:
            if h not in IGN:
                IGN.add(h); con.execute('INSERT OR IGNORE INTO ign VALUES(?,?)', (h, now)); con.commit()
            online = con.execute('SELECT sid, pagina, cidade, uf, aparelho, anuncio, ultimo FROM sess WHERE ultimo>? ORDER BY ultimo DESC',
                                 (now - ONLINE_S,)).fetchall()
            q = lambda sql, *a: con.execute(sql, a).fetchone()[0]
            visitantes = q("SELECT COUNT(DISTINCT sid) FROM ev WHERE ts>? AND tipo='view'", hoje)
            views = q("SELECT COUNT(*) FROM ev WHERE ts>? AND tipo='view'", hoje)
            ML = "tipo='click' AND COALESCE(via,'') IN ('','ml','cupom')"
            cliques = q(f"SELECT COUNT(*) FROM ev WHERE ts>? AND {ML}", hoje)
            pelo_cupom = q("SELECT COUNT(*) FROM ev WHERE ts>? AND tipo='click' AND via='cupom'", hoje)
            abriu_cupom = q("SELECT COUNT(DISTINCT sid) FROM ev WHERE ts>? AND tipo='click' AND via='abriucupom'", hoje)
            grupo = q("SELECT COUNT(*) FROM ev WHERE ts>? AND tipo='click' AND via='grupo'", hoje)
            quem_clicou = q(f"SELECT COUNT(DISTINCT sid) FROM ev WHERE ts>? AND {ML}", hoje)
            ultimos = con.execute('SELECT ts, tipo, pagina, produto, cidade, uf, aparelho, anuncio, via FROM ev ORDER BY ts DESC LIMIT 60').fetchall()
            cidades = con.execute("SELECT cidade, uf, COUNT(DISTINCT sid) n FROM ev WHERE ts>? AND cidade!='' GROUP BY cidade, uf ORDER BY n DESC LIMIT 10", (hoje,)).fetchall()
            produtos = con.execute("SELECT produto, COUNT(*) n FROM ev WHERE ts>? AND tipo='click' AND COALESCE(via,'') IN ('','ml','cupom') GROUP BY produto ORDER BY n DESC", (hoje,)).fetchall()
            anuncios = con.execute("SELECT anuncio, COUNT(DISTINCT sid) v, SUM(tipo='click' AND COALESCE(via,'') IN ('','ml','cupom')) c FROM ev WHERE ts>? AND anuncio!='' GROUP BY anuncio ORDER BY v DESC LIMIT 12", (hoje,)).fetchall()
            con.execute('DELETE FROM sess WHERE ultimo<?', (now - 86400 * 3,))
            con.commit()
        self._json(200, {
            'agora': now,
            'online': [dict(zip(['sid', 'pagina', 'cidade', 'uf', 'aparelho', 'anuncio', 'ultimo'], r)) for r in online],
            'hoje': {'visitantes': visitantes, 'paginas': views, 'cliques': cliques, 'quem_clicou': quem_clicou, 'pelo_cupom': pelo_cupom, 'abriu_cupom': abriu_cupom, 'grupo': grupo},
            'ultimos': [dict(zip(['ts', 'tipo', 'pagina', 'produto', 'cidade', 'uf', 'aparelho', 'anuncio', 'via'], r)) for r in ultimos],
            'cidades': [dict(zip(['cidade', 'uf', 'n'], r)) for r in cidades],
            'produtos': [dict(zip(['produto', 'n'], r)) for r in produtos],
            'anuncios': [dict(zip(['anuncio', 'visitantes', 'cliques'], r)) for r in anuncios],
        })


def recarrega_se_mudar():
    # o código vem do git (pull a cada minuto): reinicia sozinho quando o server.py muda
    f = os.path.abspath(__file__); m = os.path.getmtime(f)
    while True:
        time.sleep(30)
        try:
            if os.path.getmtime(f) != m:
                print('server.py mudou, reiniciando', flush=True); os.execv(sys.executable, [sys.executable, '-u', f])
        except Exception:
            pass


if __name__ == '__main__':
    import sys
    threading.Thread(target=recarrega_se_mudar, daemon=True).start()
    print(f'visitas na porta {PORT}', flush=True)
    ThreadingHTTPServer(('0.0.0.0', PORT), H).serve_forever()
