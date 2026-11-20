import os
import sqlite3
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (Flask, flash, g, redirect, render_template, request,
                    session, url_for)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dados.db")

app = Flask(__name__)

def _configuracao_obrigatoria(nomes):
    em_falta = [n for n in nomes if not os.environ.get(n)]
    if em_falta:
        raise SystemExit(
            "Defina as variáveis de ambiente antes de arrancar: "
            + ", ".join(em_falta)
            + " (ver README.md)"
        )

_configuracao_obrigatoria(["SECRET_KEY", "ADMIN_PASSWORD"])
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]


# ---- templates embebidos (aplicação em ficheiro único) ----
from jinja2 import DictLoader
TEMPLATES = {}
TEMPLATES['base.html'] = r'''<!DOCTYPE html>
<html lang="pt-PT">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block titulo %}Casas da Serra{% endblock %} — Alojamento Local, Palmela / Serra da Arrábida</title>
  <meta name="description" content="Duas casas com 2 quartos, cozinha mobilada, logradouro e estacionamento, junto à vila de Palmela, na Serra da Arrábida.">
  <style>
:root {
    --verde: #3c6e57;
    --verde-escuro: #2d5343;
    --terra: #b7884a;
    --fundo: #f7f4ee;
    --texto: #2f2f2b;
    --cartao: #ffffff;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    background: var(--fundo);
    color: var(--texto);
    line-height: 1.6;
  }
  main { max-width: 1000px; margin: 0 auto; padding: 1rem 1.25rem 3rem; }
  h1, h2, h3 { color: var(--verde-escuro); line-height: 1.25; }
  a { color: var(--verde); }
  
  /* topo */
  .topo {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: center;
    justify-content: space-between;
    background: var(--verde-escuro);
    color: #fff;
    padding: 0.9rem 1.25rem;
  }
  .marca { color: #fff; font-weight: 700; font-size: 1.2rem; text-decoration: none; }
  .marca small { display: block; font-weight: 400; opacity: 0.85; font-size: 0.75rem; }
  .topo nav { display: flex; flex-wrap: wrap; gap: 0.9rem; align-items: center; }
  .topo nav a { color: #fff; text-decoration: none; opacity: 0.9; }
  .topo nav a:hover { opacity: 1; }
  .topo nav a.ativo { text-decoration: underline; }
  
  .botao {
    display: inline-block;
    background: var(--terra);
    color: #fff !important;
    padding: 0.45rem 1rem;
    border-radius: 6px;
    text-decoration: none;
    border: none;
    font-size: 1rem;
    cursor: pointer;
  }
  .botao.grande { font-size: 1.1rem; padding: 0.7rem 1.6rem; }
  button { cursor: pointer; }
  
  /* flash */
  .flash { max-width: 1000px; margin: 0.8rem auto 0; padding: 0.7rem 1.25rem; border-radius: 6px; }
  .flash-ok { background: #ddefe4; color: #22543a; }
  .flash-erro { background: #fbe0dd; color: #7c2d23; }
  
  /* hero e secções */
  .hero { text-align: center; padding: 3rem 1rem 2rem; }
  .hero p { max-width: 46rem; margin: 1rem auto; }
  .hero.pequeno { padding: 2rem 0 0.5rem; text-align: left; }
  
  .casas { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.2rem; }
  .cartao {
    background: var(--cartao);
    border-radius: 10px;
    padding: 1.4rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }
  .detalhes { list-style: none; padding: 0; margin: 0.8rem 0; }
  .detalhes li { padding: 0.15rem 0; }
  .preco { font-size: 1.1rem; }
  .accoes { display: flex; gap: 0.8rem; align-items: center; flex-wrap: wrap; }
  
  .sobre { margin-top: 2.5rem; background: var(--cartao); border-radius: 10px; padding: 1.4rem; }
  
  /* formulários */
  .form-caixa {
    background: var(--cartao);
    border-radius: 10px;
    padding: 1.6rem;
    max-width: 520px;
    margin: 1.5rem auto;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }
  .form-caixa.estreito { max-width: 360px; margin-top: 4rem; }
  .pagina-login { min-height: 80vh; }
  form label { display: block; margin-bottom: 0.8rem; font-weight: 600; }
  form input, form select, form textarea {
    width: 100%;
    padding: 0.5rem;
    margin-top: 0.25rem;
    border: 1px solid #ccc;
    border-radius: 6px;
    font: inherit;
    background: #fff;
  }
  .linha { display: flex; gap: 1rem; flex-wrap: wrap; }
  .linha label { flex: 1; min-width: 130px; }
  .linha.fim { align-items: flex-end; }
  
  /* calendários */
  .calendarios { display: flex; flex-wrap: wrap; gap: 1rem; }
  .mes { background: var(--cartao); border-radius: 8px; padding: 0.7rem; }
  .mes h4 { margin: 0 0 0.4rem; text-align: center; color: var(--verde-escuro); }
  table.cal { border-collapse: collapse; }
  table.cal th { font-size: 0.7rem; color: #888; padding: 0.15rem 0.35rem; }
  table.cal td { width: 2rem; height: 1.9rem; text-align: center; font-size: 0.8rem; border: 1px solid #eee; background: #fff; }
  table.cal td.ocupado { background: #e6b8ad; color: #7c2d23; font-weight: 600; }
  table.cal td.passado { color: #bbb; }
  .legenda { margin-top: 0.5rem; font-size: 0.85rem; }
  .amostra { display: inline-block; width: 0.9rem; height: 0.9rem; border-radius: 3px; vertical-align: -2px; margin: 0 0.3rem 0 0.6rem; }
  .amostra.livre { background: #fff; border: 1px solid #ddd; }
  .amostra.ocupado { background: #e6b8ad; }
  
  /* gestão */
  .gestao-topo { display: flex; justify-content: space-between; align-items: center; }
  .filtros { display: flex; gap: 0.8rem; margin-bottom: 0.8rem; }
  .filtros a { text-decoration: none; padding: 0.25rem 0.7rem; border-radius: 20px; background: #e9e4da; }
  .filtros a.ativo { background: var(--verde-escuro); color: #fff; }
  .tabela { width: 100%; border-collapse: collapse; background: var(--cartao); border-radius: 8px; overflow: hidden; font-size: 0.92rem; }
  .tabela th, .tabela td { padding: 0.55rem 0.6rem; border-bottom: 1px solid #eee; text-align: left; vertical-align: top; }
  .tabela th { background: #ece7dd; }
  .tabela form { display: inline-block; margin: 0 0.2rem 0.2rem 0; }
  .tabela button, .bloqueios button { background: var(--verde); color: #fff; border: none; border-radius: 5px; padding: 0.3rem 0.6rem; font-size: 0.85rem; }
  .tabela button.perigo, .bloqueios button.perigo { background: #a94438; }
  .estado { padding: 0.15rem 0.55rem; border-radius: 12px; font-size: 0.8rem; }
  .estado-pendente { background: #fbeecb; color: #7a5c11; }
  .estado-confirmada { background: #ddefe4; color: #22543a; }
  .estado-recusada { background: #fbe0dd; color: #7c2d23; }
  .bloqueios { list-style: none; padding: 0; }
  .bloqueios li { display: flex; align-items: center; gap: 0.7rem; margin: 0.3rem 0; }
  
  footer { background: var(--verde-escuro); color: #e6efe9; padding: 1.4rem 1.25rem; text-align: center; font-size: 0.9rem; }
  footer a { color: #fff; }
  
  </style>
</head>
<body>
  <header class="topo">
    <a class="marca" href="{{ url_for('index') }}">Casas da Serra <small>Palmela · Arrábida</small></a>
    <nav>
      <a href="{{ url_for('index') }}">Início</a>
      {% for c in casas_nav %}
        <a href="{{ url_for('casa', casa_id=c['id']) }}">{{ c['nome'].split('—')[0].strip() }}</a>
      {% endfor %}
      <a class="botao" href="{{ url_for('reservar') }}">Pedir reserva</a>
    </nav>
  </header>

  {% with mensagens = get_flashed_messages(with_categories=true) %}
    {% for categoria, texto in mensagens %}
      <div class="flash flash-{{ categoria }}">{{ texto }}</div>
    {% endfor %}
  {% endwith %}

  <main>
    {% block conteudo %}{% endblock %}
  </main>

  <footer>
    <p>Casas da Serra — Alojamento Local · Jardim da Serra, Palmela, distrito de Setúbal</p>
    <p>Gerido diretamente pelo proprietário · <a href="{{ url_for('reservar') }}">Pedir reserva</a></p>
  </footer>
</body>
</html>
'''
TEMPLATES['_calendario.html'] = r'''{% macro calendario(meses) %}
{% for m in meses %}
  <div class="mes">
    <h4>{{ m['titulo'] }}</h4>
    <table class="cal">
      <thead><tr><th>Do</th><th>Se</th><th>Te</th><th>Qa</th><th>Qi</th><th>Sx</th><th>Sá</th></tr></thead>
      <tbody>
        {% for semana in m['semanas'] %}
        <tr>
          {% for dia in semana %}
          <td class="{{ 'ocupado' if dia and dia['ocupado'] else '' }}{{ ' passado' if dia and dia['passado'] else '' }}">
            {% if dia %}{{ dia['n'] }}{% endif %}
          </td>
          {% endfor %}
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
{% endfor %}
<div class="legenda"><span class="amostra livre"></span> Livre <span class="amostra ocupado"></span> Ocupado</div>
{% endmacro %}
'''
TEMPLATES['index.html'] = r'''{% extends "base.html" %}
{% block titulo %}Bem-vindo{% endblock %}
{% block conteudo %}
<section class="hero">
  <h1>Descanse na Serra da Arrábida</h1>
  <p>Duas casas acolhedoras com 2 quartos, cozinha totalmente mobilada, salão partilhado, logradouro e estacionamento — a poucos minutos da vila de Palmela, com o castelo, os vinhos da região e as praias da Arrábida à porta.</p>
  <a class="botao grande" href="{{ url_for('reservar') }}">Pedir reserva</a>
</section>

<section class="casas">
  {% for c in casas %}
  <article class="cartao">
    <h2>{{ c['nome'] }}</h2>
    <p>{{ c['descricao'] }}</p>
    <ul class="detalhes">
      <li>🛏 2 quartos</li>
      <li>🍳 Cozinha totalmente mobilada</li>
      <li>🌳 Logradouro</li>
      <li>🚗 Estacionamento</li>
    </ul>
    <p class="preco">Desde <strong>{{ '%.0f'|format(c['preco_noite']) }} €</strong> / noite</p>
    <div class="accoes">
      <a href="{{ url_for('casa', casa_id=c['id']) }}">Ver calendário</a>
      <a class="botao" href="{{ url_for('reservar', casa=c['id']) }}">Pedir reserva</a>
    </div>
  </article>
  {% endfor %}
</section>

<section class="sobre">
  <h2>A localização</h2>
  <p>Junto à vila de Palmela, na encosta da Serra da Arrábida. A 30 minutos de Lisboa e das praias de Setúbal, num ponto perfeito para caminhadas na serra, visitar o Castelo de Palmela, provar os vinhos da Península de Setúbal ou descobrir a Serra da Arrábida e o Cabo Espichel.</p>
</section>
{% endblock %}
'''
TEMPLATES['casa.html'] = r'''{% extends "base.html" %}
{% from "_calendario.html" import calendario %}
{% block titulo %}{{ casa['nome'] }}{% endblock %}
{% block conteudo %}
<section class="hero pequeno">
  <h1>{{ casa['nome'] }}</h1>
  <p>{{ casa['descricao'] }}</p>
  <p class="preco">Desde <strong>{{ '%.0f'|format(casa['preco_noite']) }} €</strong> / noite · até 6 hóspedes</p>
</section>

<section>
  <h2>Disponibilidade</h2>
  <div class="calendarios">{{ calendario(meses) }}</div>
  <p><a class="botao" href="{{ url_for('reservar', casa=casa['id']) }}">Pedir reserva nesta casa</a></p>
</section>
{% endblock %}
'''
TEMPLATES['reservar.html'] = r'''{% extends "base.html" %}
{% block titulo %}Pedir reserva{% endblock %}
{% block conteudo %}
<section class="form-caixa">
  <h1>Pedir reserva</h1>
  <p>Preencha o pedido. A sua reserva ficará <strong>pendente</strong> até ser confirmada pelo proprietário, que o contactará para o pagamento.</p>
  <form method="post">
    <label>Casa
      <select name="casa_id" required>
        {% for c in casas %}
        <option value="{{ c['id'] }}" {{ 'selected' if form.get('casa_id')|string == c['id']|string }}>{{ c['nome'] }} — {{ '%.0f'|format(c['preco_noite']) }} €/noite</option>
        {% endfor %}
      </select>
    </label>
    <div class="linha">
      <label>Check-in <input type="date" name="checkin" value="{{ form.get('checkin','') }}" required></label>
      <label>Check-out <input type="date" name="checkout" value="{{ form.get('checkout','') }}" required></label>
    </div>
    <div class="linha">
      <label>Hóspedes <input type="number" name="hospedes" min="1" max="6" value="{{ form.get('hospedes','2') }}" required></label>
    </div>
    <label>Nome <input type="text" name="nome" value="{{ form.get('nome','') }}" required></label>
    <label>Email <input type="email" name="email" value="{{ form.get('email','') }}" required></label>
    <label>Telefone <input type="tel" name="telefone" value="{{ form.get('telefone','') }}"></label>
    <label>Mensagem <textarea name="mensagem" rows="4">{{ form.get('mensagem','') }}</textarea></label>
    <button class="botao grande" type="submit">Enviar pedido</button>
  </form>
</section>
{% endblock %}
'''
TEMPLATES['obrigado.html'] = r'''{% extends "base.html" %}
{% block titulo %}Pedido enviado{% endblock %}
{% block conteudo %}
<section class="form-caixa">
  <h1>Pedido enviado, {{ nome }}! 🎉</h1>
  <p>O seu pedido de reserva na <strong>{{ casa['nome'] }}</strong>, de <strong>{{ checkin.strftime('%d/%m/%Y') }}</strong> a <strong>{{ checkout.strftime('%d/%m/%Y') }}</strong>, foi registado e está <strong>pendente de confirmação</strong>.</p>
  <p>O proprietário confirma a reserva e indica a forma de pagamento o mais breve possível.</p>
  <a class="botao" href="{{ url_for('index') }}">Voltar ao início</a>
</section>
{% endblock %}
'''
TEMPLATES['admin/login.html'] = r'''<!DOCTYPE html>
<html lang="pt-PT">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Gestão — Entrar</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body class="pagina-login">
  <div class="form-caixa estreito">
    <h1>Gestão</h1>
    {% with mensagens = get_flashed_messages(with_categories=true) %}
      {% for categoria, texto in mensagens %}<div class="flash flash-{{ categoria }}">{{ texto }}</div>{% endfor %}
    {% endwith %}
    <form method="post">
      <label>Palavra-passe <input type="password" name="password" required autofocus></label>
      <button class="botao" type="submit">Entrar</button>
    </form>
    <p><a href="{{ url_for('index') }}">← Voltar ao site</a></p>
  </div>
</body>
</html>
'''
TEMPLATES['admin/gestao.html'] = r'''{% extends "base.html" %}
{% from "_calendario.html" import calendario %}
{% block titulo %}Gestão{% endblock %}
{% block conteudo %}
<header class="gestao-topo">
  <h1>Área de gestão</h1>
  <a href="{{ url_for('logout') }}">Sair</a>
</header>

<section>
  <h2>Reservas</h2>
  <nav class="filtros">
    <a href="?estado=todas" class="{{ 'ativo' if estado == 'todas' }}">Todas</a>
    <a href="?estado=pendente" class="{{ 'ativo' if estado == 'pendente' }}">Pendentes</a>
    <a href="?estado=confirmada" class="{{ 'ativo' if estado == 'confirmada' }}">Confirmadas</a>
    <a href="?estado=recusada" class="{{ 'ativo' if estado == 'recusada' }}">Recusadas</a>
  </nav>
  <table class="tabela">
    <thead>
      <tr><th>Data pedido</th><th>Casa</th><th>Hóspede</th><th>Contactos</th><th>Datas</th><th>Hosp.</th><th>Estado</th><th>Acções</th></tr>
    </thead>
    <tbody>
      {% for r in reservas %}
      <tr>
        <td>{{ r['criada_em'][:16].replace('T', ' ') }}</td>
        <td>{{ r['casa'] }}</td>
        <td>{{ r['nome'] }}{% if r['mensagem'] %}<br><em>{{ r['mensagem'] }}</em>{% endif %}</td>
        <td>{{ r['email'] }}<br>{{ r['telefone'] }}</td>
        <td>{{ r['checkin'] }} → {{ r['checkout'] }}</td>
        <td>{{ r['hospedes'] }}</td>
        <td><span class="estado estado-{{ r['estado'] }}">{{ r['estado'] }}</span></td>
        <td>
          {% if r['estado'] != 'confirmada' %}
          <form method="post" action="{{ url_for('acao_reserva', reserva_id=r['id'], acao='confirmada') }}"><button>Confirmar</button></form>
          {% endif %}
          {% if r['estado'] != 'recusada' %}
          <form method="post" action="{{ url_for('acao_reserva', reserva_id=r['id'], acao='recusada') }}"><button class="perigo">Recusar</button></form>
          {% endif %}
        </td>
      </tr>
      {% else %}
      <tr><td colspan="8">Sem reservas.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</section>

<section>
  <h2>Bloquear datas</h2>
  <form class="linha fim" method="post" action="{{ url_for('bloquear') }}">
    <label>Casa
      <select name="casa_id">
        {% for c in casas %}<option value="{{ c['id'] }}">{{ c['nome'] }}</option>{% endfor %}
      </select>
    </label>
    <label>De <input type="date" name="inicio" required></label>
    <label>a <input type="date" name="fim" required></label>
    <button class="botao" type="submit">Bloquear</button>
  </form>
  {% if bloqueios %}
  <ul class="bloqueios">
    {% for b in bloqueios %}
    <li>{{ b['casa'] }}: {{ b['inicio'] }} → {{ b['fim'] }}
      <form method="post" action="{{ url_for('desbloquear', bloqueio_id=b['id']) }}"><button class="perigo">Remover</button></form>
    </li>
    {% endfor %}
  </ul>
  {% endif %}
</section>

<section>
  <h2>Preços por noite</h2>
  <form class="linha fim" method="post" action="{{ url_for('precos') }}">
    {% for c in casas %}
    <label>{{ c['nome'].split('—')[0].strip() }}
      <input type="text" name="preco_{{ c['id'] }}" value="{{ '%.2f'|format(c['preco_noite']) }}" inputmode="decimal">
    </label>
    {% endfor %}
    <button class="botao" type="submit">Guardar</button>
  </form>
</section>

<section>
  <h2>Calendários (próximos 3 meses)</h2>
  {% for c, meses in calendarios %}
  <h3>{{ c['nome'] }}</h3>
  <div class="calendarios">{{ calendario(meses) }}</div>
  {% endfor %}
</section>
{% endblock %}
'''
app.jinja_loader = DictLoader(TEMPLATES)


@app.context_processor
def casas_para_navegacao():
    try:
        if "db" not in g:
            g.db = sqlite3.connect(DB_PATH)
            g.db.row_factory = sqlite3.Row
        casas = g.db.execute("SELECT id, nome FROM casas ORDER BY id").fetchall()
    except sqlite3.OperationalError:
        casas = []
    return {"casas_nav": casas}


# ---------------------------------------------------------------- base de dados
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS casas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL,
            preco_noite REAL NOT NULL DEFAULT 80
        );
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            casa_id INTEGER NOT NULL REFERENCES casas(id),
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT,
            checkin TEXT NOT NULL,
            checkout TEXT NOT NULL,
            hospedes INTEGER NOT NULL DEFAULT 2,
            mensagem TEXT,
            estado TEXT NOT NULL DEFAULT 'pendente',
            criada_em TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS bloqueios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            casa_id INTEGER NOT NULL REFERENCES casas(id),
            inicio TEXT NOT NULL,
            fim TEXT NOT NULL
        );
        """
    )
    if db.execute("SELECT COUNT(*) FROM casas").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO casas (nome, descricao, preco_noite) VALUES (?, ?, ?)",
            [
                (
                    "Casa 1 — A Serra",
                    "Casa com 2 quartos, cozinha totalmente mobilada, "
                    "salão partilhado, logradouro e estacionamento. "
                    "Vista para a Serra da Arrábida, a poucos minutos da vila de Palmela.",
                    90,
                ),
                (
                    "Casa 2 — O Castelo",
                    "Casa com 2 quartos, cozinha totalmente mobilada, "
                    "salão partilhado, logradouro e estacionamento. "
                    "Ideal para conhecer Palmela, os vinhos da região e as praias da Arrábida.",
                    85,
                ),
            ],
        )
    db.commit()
    db.close()


def ocupado(casa_id, checkin, checkout, except_reserva=None):
    """True se alguma noite entre checkin (inclusive) e checkout (exclusive)
    estiver ocupada por reserva confirmada, reserva pendente ou bloqueio."""
    db = get_db()
    params = [casa_id, checkout, checkin]
    sql_reserva = (
        "SELECT COUNT(*) FROM reservas WHERE casa_id = ? AND estado IN ('pendente','confirmada') "
        "AND checkin < ? AND checkout > ?"
    )
    if except_reserva is not None:
        sql_reserva += " AND id != ?"
        params.append(except_reserva)
    n1 = db.execute(sql_reserva, params).fetchone()[0]
    n2 = db.execute(
        "SELECT COUNT(*) FROM bloqueios WHERE casa_id = ? AND inicio < ? AND fim > ?",
        [casa_id, checkout, checkin],
    ).fetchone()[0]
    return (n1 + n2) > 0


def dias_ocupados(casa_id):
    db = get_db()
    dias = set()
    for r in db.execute(
        "SELECT checkin, checkout FROM reservas WHERE casa_id = ? AND estado IN ('pendente','confirmada')",
        (casa_id,),
    ):
        d = date.fromisoformat(r["checkin"])
        fim = date.fromisoformat(r["checkout"])
        while d < fim:
            dias.add(d.isoformat())
            d += timedelta(days=1)
    for b in db.execute("SELECT inicio, fim FROM bloqueios WHERE casa_id = ?", (casa_id,)):
        d = date.fromisoformat(b["inicio"])
        fim = date.fromisoformat(b["fim"])
        while d < fim:
            dias.add(d.isoformat())
            d += timedelta(days=1)
    return dias


def calendarios(casa_id, n_meses=6):
    """Lista de meses com grelha de semanas (None = dia vazio)."""
    ocup = dias_ocupados(casa_id)
    hoje = date.today()
    meses = []
    atual = date(hoje.year, hoje.month, 1)
    for _ in range(n_meses):
        if atual.month == 12:
            proximo = date(atual.year + 1, 1, 1)
        else:
            proximo = date(atual.year, atual.month + 1, 1)
        primeiro_dia = (atual.weekday() + 1) % 7  # semana começa no domingo
        ultimo = (proximo - timedelta(days=1)).day
        dias = [None] * primeiro_dia
        for d in range(1, ultimo + 1):
            iso = atual.replace(day=d).isoformat()
            dias.append({"n": d, "iso": iso, "passado": atual.replace(day=d) < hoje,
                         "ocupado": iso in ocup})
        while len(dias) % 7 != 0:
            dias.append(None)
        semanas = [dias[i:i + 7] for i in range(0, len(dias), 7)]
        meses.append({"titulo": atual.strftime("%B de %Y").capitalize(), "semanas": semanas})
        atual = proximo
    return meses


def login_necessario(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------- site público
@app.route("/")
def index():
    db = get_db()
    casas = db.execute("SELECT * FROM casas ORDER BY id").fetchall()
    return render_template("index.html", casas=casas)


@app.route("/casa/<int:casa_id>")
def casa(casa_id):
    db = get_db()
    casa = db.execute("SELECT * FROM casas WHERE id = ?", (casa_id,)).fetchone()
    if casa is None:
        return redirect(url_for("index"))
    return render_template("casa.html", casa=casa, meses=calendarios(casa_id))


@app.route("/reservar", methods=["GET", "POST"])
def reservar():
    db = get_db()
    casas = db.execute("SELECT * FROM casas ORDER BY id").fetchall()
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        telefone = request.form.get("telefone", "").strip()
        try:
            casa_id = int(request.form.get("casa_id", ""))
            checkin = date.fromisoformat(request.form.get("checkin", ""))
            checkout = date.fromisoformat(request.form.get("checkout", ""))
            hospedes = int(request.form.get("hospedes", "2"))
        except ValueError:
            flash("Datas ou dados inválidos.", "erro")
            return render_template("reservar.html", casas=casas, form=request.form)
        mensagem = request.form.get("mensagem", "").strip()
        casa = db.execute("SELECT * FROM casas WHERE id = ?", (casa_id,)).fetchone()
        hoje = date.today()
        if casa is None:
            flash("Casa inexistente.", "erro")
        elif not nome or not email:
            flash("Nome e email são obrigatórios.", "erro")
        elif checkin < hoje or checkout <= checkin:
            flash("O check-out deve ser posterior ao check-in e as datas não podem estar no passado.", "erro")
        elif not (1 <= hospedes <= 6):
            flash("Número de hóspedes inválido (máximo 6 por casa).", "erro")
        elif ocupado(casa_id, checkin.isoformat(), checkout.isoformat()):
            flash("Essas datas já não estão disponíveis. Consulte o calendário da casa.", "erro")
        else:
            db.execute(
                "INSERT INTO reservas (casa_id, nome, email, telefone, checkin, checkout, "
                "hospedes, mensagem, estado, criada_em) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pendente', ?)",
                (casa_id, nome, email, telefone, checkin.isoformat(), checkout.isoformat(),
                 hospedes, mensagem, datetime.now().isoformat(timespec="seconds")),
            )
            db.commit()
            return render_template("obrigado.html", nome=nome, casa=casa,
                                   checkin=checkin, checkout=checkout)
        return render_template("reservar.html", casas=casas, form=request.form)
    return render_template("reservar.html", casas=casas, form={})


# ---------------------------------------------------------------- área de gestão
@app.route("/gestao/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password", "") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("gestao"))
        flash("Palavra-passe incorreta.", "erro")
    return render_template("admin/login.html")


@app.route("/gestao/logout")
@login_necessario
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/gestao")
@login_necessario
def gestao():
    db = get_db()
    estado = request.args.get("estado", "todas")
    if estado in ("pendente", "confirmada", "recusada"):
        reservas = db.execute(
            "SELECT r.*, c.nome AS casa FROM reservas r JOIN casas c ON c.id = r.casa_id "
            "WHERE r.estado = ? ORDER BY r.criada_em DESC", (estado,)
        ).fetchall()
    else:
        reservas = db.execute(
            "SELECT r.*, c.nome AS casa FROM reservas r JOIN casas c ON c.id = r.casa_id "
            "ORDER BY r.criada_em DESC"
        ).fetchall()
    casas = db.execute("SELECT * FROM casas ORDER BY id").fetchall()
    todos_calendarios = [({**c}, calendarios(c["id"], 3)) for c in casas]
    bloqueios = db.execute(
        "SELECT b.*, c.nome AS casa FROM bloqueios b JOIN casas c ON c.id = b.casa_id "
        "ORDER BY b.inicio"
    ).fetchall()
    return render_template("admin/gestao.html", reservas=reservas, estado=estado,
                           casas=casas, calendarios=todos_calendarios, bloqueios=bloqueios)


@app.route("/gestao/reserva/<int:reserva_id>/<acao>", methods=["POST"])
@login_necessario
def acao_reserva(reserva_id, acao):
    db = get_db()
    if acao in ("confirmada", "recusada"):
        r = db.execute("SELECT * FROM reservas WHERE id = ?", (reserva_id,)).fetchone()
        if r is not None:
            if acao == "confirmada" and ocupado(
                r["casa_id"], r["checkin"], r["checkout"], except_reserva=r["id"]
            ):
                flash("Não é possível confirmar: as datas já estão ocupadas.", "erro")
            else:
                db.execute("UPDATE reservas SET estado = ? WHERE id = ?", (acao, reserva_id))
                db.commit()
                flash(f"Reserva {acao}.", "ok")
    return redirect(url_for("gestao"))


@app.route("/gestao/bloquear", methods=["POST"])
@login_necessario
def bloquear():
    db = get_db()
    try:
        casa_id = int(request.form["casa_id"])
        inicio = date.fromisoformat(request.form["inicio"])
        fim = date.fromisoformat(request.form["fim"])
    except (KeyError, ValueError):
        flash("Datas de bloqueio inválidas.", "erro")
        return redirect(url_for("gestao"))
    if fim <= inicio:
        flash("A data de fim deve ser posterior à de início.", "erro")
    else:
        db.execute("INSERT INTO bloqueios (casa_id, inicio, fim) VALUES (?, ?, ?)",
                   (casa_id, inicio.isoformat(), fim.isoformat()))
        db.commit()
        flash("Datas bloqueadas.", "ok")
    return redirect(url_for("gestao"))


@app.route("/gestao/bloqueio/<int:bloqueio_id>/remover", methods=["POST"])
@login_necessario
def desbloquear(bloqueio_id):
    db = get_db()
    db.execute("DELETE FROM bloqueios WHERE id = ?", (bloqueio_id,))
    db.commit()
    flash("Bloqueio removido.", "ok")
    return redirect(url_for("gestao"))


@app.route("/gestao/precos", methods=["POST"])
@login_necessario
def precos():
    db = get_db()
    for casa in db.execute("SELECT id FROM casas").fetchall():
        campo = f"preco_{casa['id']}"
        if campo in request.form:
            try:
                preco = float(request.form[campo].replace(",", "."))
                if preco >= 0:
                    db.execute("UPDATE casas SET preco_noite = ? WHERE id = ?",
                               (preco, casa["id"]))
            except ValueError:
                pass
    db.commit()
    flash("Preços atualizados.", "ok")
    return redirect(url_for("gestao"))


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)))
