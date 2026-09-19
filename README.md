# Kinga Finance AI

Sistema de análise financeira para um pequeno comércio com várias lojas e uma fábrica:
importa vendas e custos, classifica as despesas sozinho, calcula o resultado por loja e
aponta o que precisa de atenção.

> **Sobre o “AI” do nome.** Não há modelo de linguagem nem machine learning aqui: a
> classificação de custos, os alertas e o relatório em texto saem de regras
> determinísticas, escritas para o vocabulário deste comércio. Foi uma decisão, não
> uma limitação — a categorização precisa ser **auditável** (dá para apontar qual termo
> classificou cada lançamento), **reproduzível** (o mesmo CSV dá sempre o mesmo
> resultado) e **sem custo por requisição**. Onde um modelo ajudaria de fato — o resto
> que as regras não alcançam — está no roadmap, com Ollama local.

## Sobre o projeto

Um comércio pequeno costuma fechar o mês em planilha. O dono sabe quanto entrou, mas não
quanto cada loja deu de lucro, qual categoria de custo cresceu, nem se o mês vai fechar
no azul antes de ele acabar. Os dados existem — estão soltos em notas, extratos e
lançamentos sem categoria.

O Kinga organiza esse material: recebe os lançamentos, categoriza cada custo por regras
de palavra-chave, consolida o resultado operacional por unidade e transforma isso num
painel com projeção, ranking de custos e alertas do que saiu do padrão.

## Funcionalidades

- **Classificação automática de custos** — motor de regras por palavra-chave que atribui
  categoria e subcategoria a cada despesa, com um grau de confiança proporcional à
  quantidade de termos reconhecidos, e permite sobrescrita manual.
- **Resultado operacional por loja** — receita, custo, margem e resultado calculados por
  unidade e consolidados, incluindo a fábrica e o administrativo.
- **Projeção do mês** — projeta o fechamento a partir do ritmo acumulado até o dia atual.
- **Score de saúde financeira** — índice de 0 a 100 ponderado entre margem (35),
  crescimento (25), controle de custo (25) e resultado (15), com grau qualitativo.
- **Análise de Pareto** — identifica as categorias que concentram a maior parte do custo e
  as que mais cresceram no período.
- **Alertas automáticos** — regras que sinalizam quedas de receita, custos fora da curva e
  margem abaixo do esperado, classificados por severidade.
- **Relatório em linguagem natural** — o módulo `agent` monta um resumo textual do mês a
  partir dos números calculados (geração por regras, sem modelo de linguagem).
- **Dashboard** — painel em Streamlit com gauge de saúde, waterfall de resultado,
  comparação entre lojas, série temporal, Pareto e exportação.
- **Importação e backup** — carga por CSV e backup automático do banco SQLite a cada
  inicialização da API.

## Arquitetura

```
Dashboard (Streamlit + Plotly)
        │  HTTP (httpx)
        ↓
API REST (FastAPI)
   ├── /sales      vendas
   ├── /costs      custos
   ├── /stores     lojas
   └── /report     relatório consolidado
        │
        ↓
Módulos de domínio (Python puro, sem dependência de framework)
   classifier · results · costs · billing · factory
   forecast · health · alerts · agent
        │
        ↓
SQLAlchemy ORM
        ↓
SQLite (padrão) ou PostgreSQL
```

Os módulos de domínio não conhecem FastAPI nem Streamlit: recebem uma sessão do banco e
devolvem `dataclasses`. Isso mantém a regra de negócio testável e independente da
interface — o mesmo cálculo alimenta a API, o relatório de terminal e o dashboard.

## Tecnologias

**Backend** — Python · FastAPI · SQLAlchemy 2 · Pydantic · Uvicorn
**Dashboard** — Streamlit · Plotly · pandas
**Banco** — SQLite (padrão) ou PostgreSQL via psycopg2
**Deploy** — configuração para Railway (`railway.json`)

## Instalação

Requisitos: Python 3.11+.

```bash
git clone https://github.com/devluisam/kinga-finance-ai.git
cd kinga-finance-ai

pip install -r backend/requirements.txt
pip install -r dashboard/requirements.txt

cp backend/.env.example backend/.env   # opcional: use SQLite deixando DATABASE_URL vazio

python run.py seed        # popula o banco com dados de exemplo
python run.py             # API em http://localhost:8000
python run.py dashboard   # dashboard em http://localhost:8501
```

`python run.py report` imprime o relatório do mês direto no terminal.

## Variáveis de ambiente

| Variável | Para quê |
|---|---|
| `DATABASE_URL` | Conexão do banco. Vazio = SQLite local em `data/` |
| `API_URL` | Endereço da API que o dashboard consome |

Veja `backend/.env.example`. O arquivo `.env` e os bancos em `data/` estão no `.gitignore`.

## Estrutura do projeto

```
backend/app/
├── main.py           aplicação FastAPI e backup do banco
├── database.py       engine e sessão SQLAlchemy
├── models/           Sale, Cost, Store
├── modules/          regra de negócio (classifier, results, forecast, health, alerts, agent)
├── routers/          endpoints REST
└── seed_data.py      dados de exemplo
dashboard/
├── app.py            painel Streamlit
└── components/       gráficos Plotly e UI de alertas
data/samples/         CSVs de exemplo para importação
run.py                inicializador (api | dashboard | seed | report)
```

## Roadmap

- Integração de entrada por WhatsApp (os modelos de dados já preveem o canal e o número
  de origem, mas a integração em si ainda não está implementada neste repositório).
- Testes automatizados dos módulos de domínio.

## Autor

**Luis Henrique Azevedo** — Manaus, AM
[Portfólio](https://devluisam.github.io) · [GitHub](https://github.com/devluisam) · [LinkedIn](https://www.linkedin.com/in/luis-henrique-94a6183b3)
