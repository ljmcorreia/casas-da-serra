# Casas da Serra — Alojamento Local (Palmela / Serra da Arrábida)

Aplicação web completa para gerir um alojamento local com 2 casas, tudo num único ficheiro `app.py`:

- **Site público**: apresentação das casas, calendários de disponibilidade (6 meses) e formulário de pedido de reserva.
- **Área de gestão** (`/gestao`): confirmar/recusar pedidos, bloquear datas, editar preços por noite, calendários das duas casas.

## Instalação e arranque

Requisitos: Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export SECRET_KEY="uma-chave-secreta-qualquer-longa"
export ADMIN_PASSWORD="a-sua-palavra-passe"   # a que vai usar em /gestao
python3 app.py                                # http://127.0.0.1:5000
```

- Site público: `http://127.0.0.1:5000/`
- Área de gestão: `http://127.0.0.1:5000/gestao/login`

## Dados

Tudo fica em `dados.db` (SQLite, criado automaticamente). Faça cópias deste ficheiro regularmente.

## Personalizar

- Nome da marca: pesquise "Casas da Serra" no `app.py`.
- Casas e preços iniciais: secção `init_db()` no `app.py` (preços também se mudam na área de gestão).
- Textos das páginas: dicionário `TEMPLATES` no fim do `app.py`.

## Publicar na internet (opcional)

Para hóspedes de fora, coloque a app num servidor com HTTPS (ex.: PythonAnywhere, VPS) e mantenha a palavra-passe da gestão só para si.
