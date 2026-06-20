import sys, os
# Garante que o diretório do dashboard está no path (necessário na nuvem)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import httpx
import pandas as pd
from datetime import date

from components.charts import (
    gauge_chart, donut_chart, bar_store_comparison,
    margin_bar, weekly_line, daily_bar, factory_bar,
    result_waterfall, pareto_costs as chart_pareto,
    category_trend_area, compare_bar,
)
from components.alerts_ui import render_alerts

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="Kinga Finance AI",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0F0A1A !important;
    color: #F0E6FF !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A0A3A 0%, #0F0A1A 100%) !important;
    border-right: 1px solid rgba(108,63,197,0.3);
}
[data-testid="stSidebar"] * { color: #C9B8FF !important; }

section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label { color: #9B7FE8 !important; font-size:0.8rem; }

.kpi-card {
    background: linear-gradient(135deg, rgba(108,63,197,0.25) 0%, rgba(233,30,140,0.15) 100%);
    border: 1px solid rgba(108,63,197,0.4);
    border-radius: 14px;
    padding: 20px 18px;
    text-align: center;
    backdrop-filter: blur(8px);
    transition: transform 0.2s;
}
.kpi-card:hover { transform: translateY(-2px); }
.kpi-label  { font-size:0.78rem; color:#9B7FE8; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:6px; }
.kpi-value  { font-size:1.75rem; font-weight:800; color:#F0E6FF; line-height:1.1; }
.kpi-delta  { font-size:0.82rem; margin-top:6px; }
.kpi-up     { color:#00C896; }
.kpi-down   { color:#FF4B4B; }
.kpi-neu    { color:#9B7FE8; }

.narrative-card {
    background: rgba(108,63,197,0.12);
    border: 1px solid rgba(108,63,197,0.35);
    border-radius: 14px;
    padding: 20px 24px;
    margin: 12px 0 24px 0;
    line-height: 1.75;
    font-size: 0.97rem;
    color: #D4C4FF;
}

.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #C9B8FF;
    border-left: 4px solid #6C3FC5;
    padding-left: 10px;
    margin: 28px 0 16px 0;
}

.chart-card {
    background: rgba(26,16,51,0.8);
    border: 1px solid rgba(108,63,197,0.2);
    border-radius: 12px;
    padding: 4px;
}

.store-table th {
    background: rgba(108,63,197,0.3) !important;
    color: #C9B8FF !important;
}

div[data-testid="stMetric"] {
    background: rgba(26,16,51,0.6);
    border: 1px solid rgba(108,63,197,0.25);
    border-radius: 10px;
    padding: 12px 16px;
}
div[data-testid="stMetricLabel"] { color: #9B7FE8 !important; }
div[data-testid="stMetricValue"] { color: #F0E6FF !important; }

.stDataFrame { background: transparent !important; }
thead tr th { background: rgba(108,63,197,0.3) !important; color: #C9B8FF !important; }
tbody tr:nth-child(even) { background: rgba(108,63,197,0.07) !important; }

hr { border-color: rgba(108,63,197,0.25) !important; }

.stTabs [data-baseweb="tab-list"] {
    background: rgba(26,16,51,0.6);
    border-radius: 10px;
    gap: 4px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #9B7FE8 !important;
    border-radius: 8px;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: rgba(108,63,197,0.4) !important;
    color: #F0E6FF !important;
}

.status-lucro   { color:#00C896; font-weight:800; font-size:1.1rem; }
.status-prejuizo{ color:#FF4B4B; font-weight:800; font-size:1.1rem; }

.tx-card {
    display: flex;
    align-items: center;
    background: rgba(26,16,51,0.8);
    border-radius: 12px;
    padding: 14px 18px;
    margin: 6px 0;
    border-left: 4px solid transparent;
    transition: transform 0.15s;
}
.tx-card:hover { transform: translateX(3px); }
.tx-entrada { border-left-color: #00C896; }
.tx-saida   { border-left-color: #FF4B4B; }
.tx-icon    { font-size: 1.4rem; margin-right: 14px; }
.tx-body    { flex: 1; }
.tx-desc    { font-size: 0.95rem; font-weight: 600; color: #F0E6FF; }
.tx-meta    { font-size: 0.78rem; color: #6C3FC5; margin-top: 2px; }
.tx-right   { text-align: right; }
.tx-amount-entrada { font-size: 1.1rem; font-weight: 800; color: #00C896; }
.tx-amount-saida   { font-size: 1.1rem; font-weight: 800; color: #FF4B4B; }
.badge {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    margin-top: 4px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.badge-receita   { background: rgba(0,200,150,0.15); color: #00C896; border: 1px solid rgba(0,200,150,0.3); }
.badge-fab       { background: rgba(108,63,197,0.2);  color: #C9B8FF; border: 1px solid rgba(108,63,197,0.4); }
.badge-loja      { background: rgba(233,30,140,0.15); color: #FF6EC7; border: 1px solid rgba(233,30,140,0.3); }
.badge-admin     { background: rgba(255,165,0,0.15);  color: #FFB347; border: 1px solid rgba(255,165,0,0.3); }
.badge-outros    { background: rgba(255,255,255,0.07); color: #9B7FE8; border: 1px solid rgba(255,255,255,0.1); }
.wa-stat-box {
    background: linear-gradient(135deg, rgba(37,211,102,0.1) 0%, rgba(18,140,126,0.1) 100%);
    border: 1px solid rgba(37,211,102,0.25);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}
.wa-stat-label { font-size: 0.75rem; color: #25D366; letter-spacing: 0.08em; text-transform: uppercase; }
.wa-stat-value { font-size: 1.6rem; font-weight: 800; color: #F0E6FF; margin: 4px 0; }
.wa-stat-sub   { font-size: 0.8rem; color: #9B7FE8; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────
MONTHS_PT = {
    1:"Janeiro", 2:"Fevereiro", 3:"Março", 4:"Abril",
    5:"Maio", 6:"Junho", 7:"Julho", 8:"Agosto",
    9:"Setembro", 10:"Outubro", 11:"Novembro", 12:"Dezembro",
}

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:10px 0 20px 0;">
        <div style="font-size:2.5rem;">🍇</div>
        <div style="font-size:1.2rem;font-weight:800;color:#C9B8FF;">Kinga Finance AI</div>
        <div style="font-size:0.75rem;color:#6C3FC5;margin-top:4px;">Agente Financeiro Autônomo</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Período**")
    _hoje = date.today()
    year  = st.selectbox("Ano",  [2026, 2025], index=0 if _hoje.year == 2026 else 1, label_visibility="collapsed")
    month = st.selectbox("Mês",  list(range(1, 13)), index=_hoje.month - 1,
                         format_func=lambda m: MONTHS_PT[m], label_visibility="collapsed")
    refresh = st.button("↻ Atualizar dados", use_container_width=True)

    st.markdown("---")

    st.markdown("""
    <div style="font-size:0.75rem;color:#4A3570;text-align:center;padding-top:4px;">
        Kinga Açaí Frozen · v1.1<br>
        <span style="color:#6C3FC5;">● API conectada</span>
    </div>
    """, unsafe_allow_html=True)


# ── Data fetch ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def fetch_report(year: int, month: int) -> dict | None:
    try:
        r = httpx.get(f"{API_URL}/report/{year}/{month}", timeout=15)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        return None
    except Exception as e:
        st.error(f"Erro: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_annual(year: int) -> dict | None:
    try:
        r = httpx.get(f"{API_URL}/report/annual/{year}", timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

if refresh:
    st.cache_data.clear()

data = fetch_report(year, month)

if data is None:
    st.markdown("""
    <div style="text-align:center;padding:80px 0;">
        <div style="font-size:3rem;">⚡</div>
        <h2 style="color:#FF4B4B;">API não encontrada</h2>
        <p style="color:#9B7FE8;">Inicie o backend antes de abrir o dashboard:</p>
        <code style="background:rgba(108,63,197,0.2);padding:8px 16px;border-radius:6px;color:#C9B8FF;">
            python run.py
        </code>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

result    = data.get("result", {})
stores    = data.get("store_results", [])
factory   = data.get("factory", {})
cat_costs = data.get("costs_by_category", {})
subcat    = data.get("costs_by_subcategory", [])
weekly    = data.get("weekly_revenue", [])
alerts    = data.get("alerts", [])
forecast     = data.get("forecast", {})
health       = data.get("health", {})
channels     = data.get("channel_revenue", {})
top_costs_d  = data.get("top_costs", [])
growing_c_d  = data.get("growing_costs", [])
pareto_d     = data.get("pareto_costs", [])
daily_rev    = data.get("daily_revenue", [])
narrative    = data.get("narrative", "")
period       = data.get("period", f"{month:02d}/{year}")

fat   = result.get("faturamento", 0)
custo = result.get("custos", 0)
res   = result.get("resultado", 0)
marg  = result.get("margem_pct", 0)
vfat  = result.get("variacao_faturamento", 0)
vcust = result.get("variacao_custos", 0)
status= result.get("status", "—")


# ── Header ──────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(f"## 🍇 Kinga Finance AI")
    st.markdown(f"<span style='color:#6C3FC5;font-size:0.9rem;'>Relatório de **{MONTHS_PT[month]} {year}** · Kinga Açaí Frozen</span>",
                unsafe_allow_html=True)
with col_h2:
    status_class = "status-lucro" if status == "LUCRO" else "status-prejuizo"
    st.markdown(f"<div style='text-align:right;padding-top:12px;'><span class='{status_class}'>{status}</span></div>",
                unsafe_allow_html=True)

st.markdown("---")


# ── Narrativa ────────────────────────────────────────────────────────────────
narrative_clean = (
    narrative
    .replace("✅", "").replace("❌", "").replace("⚠️", "")
    .replace("📊", "").replace("🏭", "").replace("🚨", "")
    .replace("**", "").strip()
)
if narrative_clean:
    st.markdown(f'<div class="narrative-card">🤖 <strong>Análise do Agente</strong><br><br>{narrative_clean.replace(chr(10), "<br>")}</div>',
                unsafe_allow_html=True)


# ── KPIs ─────────────────────────────────────────────────────────────────────
def delta_html(v: float, invert: bool = False) -> str:
    up = v >= 0 if not invert else v <= 0
    cls = "kpi-up" if up else "kpi-down"
    sign = "▲" if v >= 0 else "▼"
    return f'<span class="{cls}">{sign} {abs(v):.1f}% vs mês ant.</span>'

k1, k2, k3, k4 = st.columns(4)
kpis = [
    (k1, "💰 Faturamento",  f"R$ {fat:,.2f}",      delta_html(vfat)),
    (k2, "💸 Custos Totais", f"R$ {custo:,.2f}",   delta_html(vcust, invert=True)),
    (k3, "📈 Resultado",     f"R$ {res:,.2f}",      f'<span class="{"kpi-up" if res>=0 else "kpi-down"}">{status}</span>'),
    (k4, "🎯 Margem Op.",    f"{marg:.1f}%",        f'<span class="kpi-neu">Custo: {result.get("custo_pct",0):.1f}%</span>'),
]
for col, label, value, delta in kpis:
    with col:
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-delta">{delta}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Health Score ──────────────────────────────────────────────────────────────
if health:
    _hs = health.get("score", 0)
    _hg = health.get("grade", "—")
    _hc = health.get("grade_color", "#9B7FE8")
    _det = health.get("detalhes", {})
    _dim_labels = {"margem": "Margem", "crescimento": "Crescimento",
                   "controle_custo": "Custo Ctrl", "resultado": "Resultado"}
    _dim_maxes = {"margem": 35, "crescimento": 25, "controle_custo": 25, "resultado": 15}
    dims_html = "".join(
        f'<div style="flex:1;text-align:center;">'
        f'<div style="font-size:.65rem;color:#6C3FC5;margin-bottom:3px;">{_dim_labels.get(k,k)}</div>'
        f'<div style="background:rgba(108,63,197,0.15);border-radius:4px;height:6px;overflow:hidden;">'
        f'<div style="width:{int(v/_dim_maxes.get(k,1)*100)}%;background:{_hc};height:6px;"></div>'
        f'</div>'
        f'<div style="font-size:.65rem;color:#9B7FE8;margin-top:2px;">{v}/{_dim_maxes.get(k,1)}</div>'
        f'</div>'
        for k, v in _det.items()
    )
    st.markdown(
        f'<div style="background:rgba(26,16,51,0.8);border:1px solid rgba(108,63,197,0.25);'
        f'border-radius:12px;padding:14px 20px;margin-bottom:4px;">'
        f'<div style="display:flex;align-items:center;gap:16px;margin-bottom:8px;">'
        f'<div style="font-size:0.78rem;color:#9B7FE8;text-transform:uppercase;letter-spacing:.08em;min-width:110px;">🏥 Saúde Financeira</div>'
        f'<div style="flex:1;background:rgba(108,63,197,0.15);border-radius:20px;height:10px;">'
        f'<div style="width:{int(_hs)}%;background:{_hc};border-radius:20px;height:10px;"></div>'
        f'</div>'
        f'<div style="font-size:1.1rem;font-weight:800;color:{_hc};min-width:60px;text-align:right;">{_hs:.0f}<span style="font-size:.7rem;color:#9B7FE8;">/100</span></div>'
        f'<div style="font-size:.85rem;font-weight:700;color:{_hc};min-width:70px;">{_hg}</div>'
        f'</div>'
        f'<div style="display:flex;gap:12px;">{dims_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Forecast (projeção de fechamento) ─────────────────────────────────────────
if forecast and forecast.get("dias_restantes", 0) > 0:
    _fp   = forecast.get("fat_projetado", 0)
    _fd   = forecast.get("fat_diario", 0)
    _dr   = forecast.get("dias_restantes", 0)
    _pct  = forecast.get("pct_mes_decorrido", 0)
    _tend = forecast.get("tendencia", "")
    _tend_label = {"ACIMA": "▲ acima do mês ant.", "ABAIXO": "▼ abaixo do mês ant.",
                   "NO_RITMO": "≈ no ritmo do mês ant."}.get(_tend, "")
    _tend_color = {"ACIMA": "#00C896", "ABAIXO": "#FF4B4B"}.get(_tend, "#9B7FE8")
    st.markdown(
        f'<div style="background:rgba(26,16,51,0.8);border:1px solid rgba(108,63,197,0.25);'
        f'border-radius:12px;padding:14px 20px;margin-bottom:16px;">'
        f'<div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap;">'
        f'<div style="font-size:0.78rem;color:#9B7FE8;text-transform:uppercase;letter-spacing:.08em;">📅 Projeção de Fechamento</div>'
        f'<div style="font-size:1.15rem;font-weight:800;color:#F0E6FF;">R$ {_fp:,.2f}</div>'
        f'<div style="font-size:0.82rem;color:{_tend_color};">{_tend_label}</div>'
        f'<div style="margin-left:auto;font-size:0.8rem;color:#6C3FC5;">'
        f'{_pct:.0f}% do mês · R$ {_fd:,.2f}/dia · {_dr} dias restantes'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# ── Abas principais ───────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Visão Geral", "🏪 Por Loja", "🏭 Fábrica",
    "📋 Detalhado", "📈 Tendência Anual", "✏️ Lançamentos",
])


# ── TAB 1: Visão Geral ────────────────────────────────────────────────────────
with tab1:
    c1, c2, c3 = st.columns([1, 1.4, 1.6])

    with c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(gauge_chart(marg, "Margem Operacional"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        if cat_costs:
            st.plotly_chart(
                donut_chart(list(cat_costs.keys()), list(cat_costs.values()), "Custos por Categoria"),
                use_container_width=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(weekly_line(weekly), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card" style="margin-top:16px;">', unsafe_allow_html=True)
    st.plotly_chart(result_waterfall(fat, custo, res), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Canal de vendas
    if channels:
        import plotly.graph_objects as go
        _ch_labels = {"pdv": "Balcão (PDV)", "ifood": "iFood",
                      "delivery": "Delivery", "whatsapp": "WhatsApp"}
        _ch_names = [_ch_labels.get(k, k) for k in channels]
        _ch_vals = list(channels.values())
        fig_ch = go.Figure(go.Pie(
            labels=_ch_names, values=_ch_vals, hole=0.55,
            marker_colors=["#6C3FC5", "#E91E8C", "#00C896", "#FFB347"],
            textinfo="label+percent", textfont_size=11,
        ))
        fig_ch.update_layout(
            title=dict(text="Receitas por Canal", font=dict(color="#C9B8FF", size=13)),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#C9B8FF"), showlegend=False,
            margin=dict(t=40, b=10, l=10, r=10), height=240,
        )
        st.markdown('<div class="chart-card" style="margin-top:16px;">', unsafe_allow_html=True)
        st.plotly_chart(fig_ch, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Alertas inline
    st.markdown('<div class="section-title">Alertas Inteligentes</div>', unsafe_allow_html=True)
    render_alerts(alerts)


# ── TAB 2: Por Loja ───────────────────────────────────────────────────────────
with tab2:
    if not stores:
        st.info("Sem dados de lojas para este período.")
    else:
        ca, cb = st.columns(2)
        with ca:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.plotly_chart(bar_store_comparison(stores), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with cb:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.plotly_chart(margin_bar(stores), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">Ranking Detalhado</div>', unsafe_allow_html=True)

        df_s = pd.DataFrame(stores)
        if not df_s.empty and "store_name" in df_s.columns:
            df_s = df_s.sort_values("faturamento", ascending=False)

            # Melhor e pior
            m1, m2, m3, m4 = st.columns(4)
            melhor = df_s.loc[df_s["margem_pct"].idxmax()]
            pior   = df_s.loc[df_s["margem_pct"].idxmin()]
            maior_fat = df_s.loc[df_s["faturamento"].idxmax()]
            maior_custo = df_s.loc[df_s["custos"].idxmax()]

            m1.metric("🏆 Melhor Margem",   melhor["store_name"],  f"{melhor['margem_pct']:.1f}%")
            m2.metric("⚠️ Menor Margem",    pior["store_name"],    f"{pior['margem_pct']:.1f}%")
            m3.metric("💰 Maior Fat.",       maior_fat["store_name"], f"R$ {maior_fat['faturamento']:,.0f}")
            m4.metric("💸 Maior Custo",      maior_custo["store_name"], f"R$ {maior_custo['custos']:,.0f}")

            st.markdown("<br>", unsafe_allow_html=True)

            # Tabela
            df_show = df_s[["store_name", "faturamento", "custos", "resultado", "margem_pct"]].copy()
            df_show.columns = ["Loja", "Faturamento", "Custos", "Resultado", "Margem %"]
            df_show["Faturamento"] = df_show["Faturamento"].apply(lambda v: f"R$ {v:,.2f}")
            df_show["Custos"]      = df_show["Custos"].apply(lambda v: f"R$ {v:,.2f}")
            df_show["Resultado"]   = df_show["Resultado"].apply(lambda v: f"R$ {v:,.2f}")
            df_show["Margem %"]    = df_show["Margem %"].apply(lambda v: f"{v:.1f}%")
            st.dataframe(df_show, use_container_width=True, hide_index=True, height=200)


# ── TAB 3: Fábrica ────────────────────────────────────────────────────────────
with tab3:
    if not factory or factory.get("custos_totais", 0) == 0:
        st.info("Sem dados de fábrica para este período.")
    else:
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Custo Total",      f"R$ {factory['custos_totais']:,.2f}")
        f2.metric("% do Faturamento", f"{factory['pct_faturamento']:.1f}%")
        f3.metric("Peso da Folha",    f"{factory['peso_folha']:.1f}%",
                  delta="Acima do ideal" if factory["peso_folha"] > 35 else "OK",
                  delta_color="inverse" if factory["peso_folha"] > 35 else "normal")
        f4.metric("Mat. Prima",       f"R$ {factory['materia_prima']:,.2f}")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(factory_bar(factory), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Breakdown
        st.markdown('<div class="section-title">Composição Detalhada</div>', unsafe_allow_html=True)
        total_fab = factory["custos_totais"]
        items = [
            ("Matéria-prima", factory["materia_prima"]),
            ("Folha de Pagamento", factory["folha"]),
            ("Energia", factory["energia"]),
            ("Frete", factory["frete"]),
            ("Outros", factory["outros"]),
        ]
        cols = st.columns(len(items))
        for col, (label, val) in zip(cols, items):
            pct = val / total_fab * 100 if total_fab > 0 else 0
            col.metric(label, f"R$ {val:,.2f}", f"{pct:.1f}% do total")


# ── TAB 4: Detalhado ──────────────────────────────────────────────────────────
with tab4:
    if subcat:
        st.markdown('<div class="section-title">Todos os Custos Classificados</div>',
                    unsafe_allow_html=True)

        df_c = pd.DataFrame(subcat)
        if not df_c.empty:
            # Filtro por categoria
            cats = ["Todas"] + sorted(df_c["categoria"].unique().tolist())
            cat_filter = st.selectbox("Filtrar por categoria", cats)

            if cat_filter != "Todas":
                df_c = df_c[df_c["categoria"] == cat_filter]

            df_c = df_c.sort_values("valor", ascending=False)
            total_filtrado = df_c["valor"].sum()
            st.caption(f"Total filtrado: **R$ {total_filtrado:,.2f}**")

            df_c["valor"] = df_c["valor"].apply(lambda v: f"R$ {v:,.2f}")
            df_c.columns = ["Categoria", "Subcategoria", "Valor (R$)"]
            st.dataframe(df_c, use_container_width=True, hide_index=True, height=400)
    else:
        st.info("Sem dados de custos para este período.")

    # Upload CSV
    st.markdown('<div class="section-title">Importar Dados</div>', unsafe_allow_html=True)
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        st.markdown("**Importar Vendas (CSV)**")
        f_sales = st.file_uploader("vendas.csv", type="csv", key="sales_up",
                                    help="Colunas: date, store_id, store_name, channel, amount")
        if f_sales and st.button("Enviar Vendas"):
            try:
                r = httpx.post(f"{API_URL}/sales/upload-csv",
                               files={"file": (f_sales.name, f_sales, "text/csv")}, timeout=30)
                r.raise_for_status()
                st.success(f"Importadas {r.json()['importados']} vendas!")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Erro: {e}")

    with col_up2:
        st.markdown("**Importar Custos (CSV)**")
        f_costs = st.file_uploader("custos.csv", type="csv", key="costs_up",
                                    help="Colunas: date, description, amount, unit")
        if f_costs and st.button("Enviar Custos"):
            try:
                r = httpx.post(f"{API_URL}/costs/upload-csv",
                               files={"file": (f_costs.name, f_costs, "text/csv")}, timeout=30)
                r.raise_for_status()
                st.success(f"Importados {r.json()['importados']} custos!")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Erro: {e}")

# ── TAB 5: Tendência Anual ───────────────────────────────────────────────────
with tab5:
    import plotly.graph_objects as go

    annual_data = fetch_annual(year)
    if not annual_data:
        st.info("Sem dados anuais disponíveis.")
    else:
        months_data = annual_data.get("months", [])
        total_fat_y = annual_data.get("total_faturamento", 0)
        total_custo_y = annual_data.get("total_custos", 0)
        total_res_y = annual_data.get("total_resultado", 0)

        ay1, ay2, ay3 = st.columns(3)
        ay1.metric("Faturamento Anual", f"R$ {total_fat_y:,.2f}")
        ay2.metric("Custos Anuais", f"R$ {total_custo_y:,.2f}")
        ay3.metric("Resultado Anual", f"R$ {total_res_y:,.2f}",
                   delta="LUCRO" if total_res_y >= 0 else "PREJUÍZO")

        st.markdown("<br>", unsafe_allow_html=True)

        names = [m["month_short"] for m in months_data]
        fats  = [m["faturamento"] for m in months_data]
        costs = [m["custos"] for m in months_data]
        margins = [m["margem_pct"] for m in months_data]

        # Gráfico barras faturamento + custos
        fig_ann = go.Figure()
        fig_ann.add_trace(go.Bar(name="Faturamento", x=names, y=fats,
                                  marker_color="#6C3FC5"))
        fig_ann.add_trace(go.Bar(name="Custos", x=names, y=costs,
                                  marker_color="#E91E8C"))
        fig_ann.update_layout(
            title=dict(text=f"Faturamento vs Custos — {year}", font=dict(color="#C9B8FF", size=14)),
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#C9B8FF"),
            xaxis=dict(gridcolor="rgba(108,63,197,0.2)"),
            yaxis=dict(gridcolor="rgba(108,63,197,0.2)", tickprefix="R$ "),
            legend=dict(font=dict(color="#C9B8FF")),
            margin=dict(t=50, b=20, l=20, r=20), height=320,
        )
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(fig_ann, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Gráfico linha de margem
        st.markdown("<br>", unsafe_allow_html=True)
        fig_mg = go.Figure()
        fig_mg.add_trace(go.Scatter(
            x=names, y=margins, mode="lines+markers+text",
            line=dict(color="#00C896", width=2),
            marker=dict(size=7),
            text=[f"{v:.1f}%" for v in margins],
            textposition="top center",
            textfont=dict(size=10, color="#C9B8FF"),
            name="Margem %",
        ))
        fig_mg.add_hline(y=15, line_dash="dot", line_color="#FFB347",
                         annotation_text="Mínimo ideal (15%)",
                         annotation_font=dict(color="#FFB347", size=10))
        fig_mg.update_layout(
            title=dict(text=f"Margem Operacional Mensal — {year}", font=dict(color="#C9B8FF", size=14)),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#C9B8FF"),
            xaxis=dict(gridcolor="rgba(108,63,197,0.2)"),
            yaxis=dict(gridcolor="rgba(108,63,197,0.2)", ticksuffix="%"),
            margin=dict(t=50, b=20, l=20, r=20), height=280,
        )
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(fig_mg, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Tabela resumo
        st.markdown('<div class="section-title">Resumo Mensal</div>', unsafe_allow_html=True)
        df_ann = pd.DataFrame(months_data)
        if not df_ann.empty:
            df_show_ann = df_ann[["month_name","faturamento","custos","resultado","margem_pct"]].copy()
            df_show_ann.columns = ["Mês","Faturamento","Custos","Resultado","Margem %"]
            for c in ["Faturamento","Custos","Resultado"]:
                df_show_ann[c] = df_show_ann[c].apply(lambda v: f"R$ {v:,.2f}")
            df_show_ann["Margem %"] = df_show_ann["Margem %"].apply(lambda v: f"{v:.1f}%")
            st.dataframe(df_show_ann, use_container_width=True, hide_index=True)


# ── TAB 6: Lançamentos ───────────────────────────────────────────────────────
with tab6:

    # ── Helpers de dados ──────────────────────────────────────────────────────
    @st.cache_data(ttl=3600)
    def fetch_meta() -> dict:
        try:
            r = httpx.get(f"{API_URL}/costs/categories", timeout=5)
            return r.json()
        except Exception:
            return {"categories": ["Fábrica", "Lojas", "Administrativo", "Outros"],
                    "subcategories": {}, "units": ["fabrica", "loja_01", "loja_02", "loja_03", "admin"]}

    @st.cache_data(ttl=30)
    def fetch_stores() -> list[dict]:
        try:
            r = httpx.get(f"{API_URL}/stores/", timeout=5)
            return r.json()
        except Exception:
            return []

    meta       = fetch_meta()
    CATS       = meta.get("categories", [])
    SUBCS      = meta.get("subcategories", {})
    UNITS_META = meta.get("units", [])
    CHANNELS   = ["pdv", "ifood", "delivery"]

    all_stores  = fetch_stores()
    active_stores = [s for s in all_stores if s["active"]]
    UNIT_LABELS = {s["store_id"]: s["store_name"] for s in all_stores}
    UNIT_LABELS.update({"fabrica": "Fábrica", "admin": "Administrativo"})

    # Lojas de venda (excluindo fabrica e admin)
    STORE_TUPLES = [(s["store_id"], s["store_name"])
                    for s in active_stores
                    if s["store_id"] not in ("fabrica", "admin")]
    if not STORE_TUPLES:
        STORE_TUPLES = [("loja_01","Loja Centro"),("loja_02","Loja Shopping"),("loja_03","Loja Norte")]

    # Todas as unidades para custos
    UNITS_ALL = [s["store_id"] for s in all_stores] or UNITS_META

    subtab_a, subtab_b, subtab_c, subtab_d, subtab_e, subtab_f = st.tabs([
        "➕ Nova Venda", "➕ Novo Custo", "📄 Gerenciar Vendas", "📄 Gerenciar Custos",
        "🏪 Lojas", "🔒 Segurança",
    ])

    # ── SUB-TAB A: Nova Venda ─────────────────────────────────────────────────
    with subtab_a:
        st.markdown('<div class="section-title">Registrar Venda</div>', unsafe_allow_html=True)

        with st.form("form_venda", clear_on_submit=True):
            fc1, fc2 = st.columns(2)
            with fc1:
                v_date    = st.date_input("Data", value=date(year, month, 1))
                v_store   = st.selectbox("Loja", STORE_TUPLES, format_func=lambda s: s[1])
                v_channel = st.selectbox("Canal", CHANNELS,
                                         format_func=lambda c: {"pdv":"Balcão (PDV)","ifood":"iFood","delivery":"Delivery"}.get(c, c))
            with fc2:
                v_amount  = st.number_input("Valor (R$)", min_value=0.01, step=0.01, format="%.2f")
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("✅ Salvar Venda", use_container_width=True)

            if submitted:
                if v_amount <= 0:
                    st.error("Valor deve ser maior que zero.")
                else:
                    try:
                        r = httpx.post(f"{API_URL}/sales/", json={
                            "date": str(v_date),
                            "store_id":   v_store[0],
                            "store_name": v_store[1],
                            "channel":    v_channel,
                            "amount":     v_amount,
                        }, timeout=10)
                        r.raise_for_status()
                        st.success(f"Venda de R$ {v_amount:,.2f} registrada para {v_store[1]}!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

        st.markdown("---")
        st.markdown("**Ou importe via CSV**")
        st.caption("Formato: `date, store_id, store_name, channel, amount`")
        with st.expander("Ver exemplo de CSV"):
            st.code(
                "date,store_id,store_name,channel,amount\n"
                "2026-05-10,loja_01,Loja Centro,pdv,1850.00\n"
                "2026-05-10,loja_02,Loja Shopping,ifood,920.50"
            )
        f_sales = st.file_uploader("Selecione o CSV de vendas", type="csv", key="sales_csv")
        if f_sales:
            preview = pd.read_csv(f_sales)
            st.dataframe(preview.head(5), use_container_width=True, hide_index=True)
            f_sales.seek(0)
            if st.button("📤 Importar Vendas", use_container_width=True):
                try:
                    r = httpx.post(f"{API_URL}/sales/upload-csv",
                                   files={"file": (f_sales.name, f_sales, "text/csv")}, timeout=30)
                    r.raise_for_status()
                    st.success(f"{r.json()['importados']} vendas importadas!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Erro: {e}")

    # ── SUB-TAB B: Novo Custo ─────────────────────────────────────────────────
    with subtab_b:
        st.markdown('<div class="section-title">Registrar Custo</div>', unsafe_allow_html=True)
        st.caption("Preencha a descrição que o agente classifica automaticamente. Você pode revisar a seguir.")

        with st.form("form_custo", clear_on_submit=True):
            fd1, fd2 = st.columns(2)
            with fd1:
                c_date = st.date_input("Data", value=date(year, month, 1), key="c_date")
                c_desc = st.text_input("Descrição do pagamento",
                                       placeholder="Ex: Conta de luz fábrica CEMIG")
                c_amount = st.number_input("Valor (R$)", min_value=0.01, step=0.01,
                                           format="%.2f", key="c_amount")
            with fd2:
                c_unit = st.selectbox("Unidade", UNITS_ALL,
                                      format_func=lambda u: UNIT_LABELS.get(u, u))
                c_cat  = st.selectbox("Categoria (opcional — classifica automático se vazio)",
                                      ["— automático —"] + CATS)
                c_subcat_opts = SUBCS.get(c_cat, []) if c_cat != "— automático —" else []
                c_subcat = st.selectbox("Subcategoria", ["—"] + c_subcat_opts) if c_subcat_opts else st.selectbox("Subcategoria", ["—"])
                submitted_c = st.form_submit_button("✅ Salvar Custo", use_container_width=True)

            if submitted_c:
                if not c_desc.strip():
                    st.error("Informe a descrição do custo.")
                elif c_amount <= 0:
                    st.error("Valor deve ser maior que zero.")
                else:
                    payload = {
                        "date": str(c_date), "description": c_desc,
                        "amount": c_amount, "unit": c_unit,
                    }
                    if c_cat != "— automático —":
                        payload["category"]    = c_cat
                        payload["subcategory"] = c_subcat if c_subcat != "—" else ""
                    try:
                        r = httpx.post(f"{API_URL}/costs/", json=payload, timeout=10)
                        r.raise_for_status()
                        resp = r.json()
                        st.success(
                            f"Custo salvo! Classificado como: **{resp['category']} / {resp['subcategory']}** "
                            f"· Unidade: **{UNIT_LABELS.get(resp['unit'], resp['unit'])}**"
                        )
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

        st.markdown("---")
        st.markdown("**Ou importe via CSV**")
        st.caption("Formato: `date, description, amount, unit`")
        with st.expander("Ver exemplo de CSV"):
            st.code(
                "date,description,amount,unit\n"
                "2026-05-05,Compra açaí polpa fornecedor,4800.00,fabrica\n"
                "2026-05-05,Aluguel loja 1 Centro,2800.00,loja_01\n"
                "2026-05-05,DAS Simples Nacional,1450.00,admin"
            )
        f_costs = st.file_uploader("Selecione o CSV de custos", type="csv", key="costs_csv")
        if f_costs:
            preview_c = pd.read_csv(f_costs)
            st.dataframe(preview_c.head(5), use_container_width=True, hide_index=True)
            f_costs.seek(0)
            if st.button("📤 Importar Custos", use_container_width=True):
                try:
                    r = httpx.post(f"{API_URL}/costs/upload-csv",
                                   files={"file": (f_costs.name, f_costs, "text/csv")}, timeout=30)
                    r.raise_for_status()
                    st.success(f"{r.json()['importados']} custos importados!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Erro: {e}")

    # ── SUB-TAB C: Gerenciar Vendas ───────────────────────────────────────────
    with subtab_c:
        st.markdown('<div class="section-title">Vendas do Período</div>', unsafe_allow_html=True)

        @st.cache_data(ttl=10)
        def fetch_sales(m, y):
            try:
                r = httpx.get(f"{API_URL}/sales/", params={"month": m, "year": y}, timeout=10)
                return r.json()
            except Exception:
                return []

        sales_data = fetch_sales(month, year)

        if not sales_data:
            st.info("Sem vendas lançadas para este período.")
        else:
            df_s = pd.DataFrame(sales_data)
            st.caption(f"**{len(df_s)} registros** · Total: R$ {df_s['amount'].sum():,.2f}")

            sf1, sf2 = st.columns(2)
            with sf1:
                lojas_f  = ["Todas"] + sorted(df_s["store_name"].unique().tolist())
                loja_sel = st.selectbox("Filtrar loja", lojas_f, key="sf_loja")
            with sf2:
                canais_f  = ["Todos"] + sorted(df_s["channel"].unique().tolist())
                canal_sel = st.selectbox("Filtrar canal", canais_f, key="sf_canal")

            df_view = df_s.copy()
            if loja_sel != "Todas": df_view = df_view[df_view["store_name"] == loja_sel]
            if canal_sel != "Todos": df_view = df_view[df_view["channel"] == canal_sel]
            df_view = df_view.sort_values("date", ascending=False)
            df_view["amount_fmt"]  = df_view["amount"].apply(lambda v: f"R$ {v:,.2f}")
            df_view["channel_fmt"] = df_view["channel"].map(
                {"pdv":"Balcão","ifood":"iFood","delivery":"Delivery","whatsapp":"WhatsApp"}
            ).fillna(df_view["channel"])
            df_view["desc_fmt"] = df_view.get("description", pd.Series([""] * len(df_view))).fillna("")

            st.dataframe(
                df_view[["id","date","store_name","channel_fmt","desc_fmt","amount_fmt","source"]].rename(
                    columns={"id":"ID","date":"Data","store_name":"Loja",
                             "channel_fmt":"Canal","desc_fmt":"Descrição",
                             "amount_fmt":"Valor","source":"Origem"}
                ),
                use_container_width=True, hide_index=True, height=280,
            )

        st.markdown("---")

        # ── Editar venda ───────────────────────────────────────────────────
        with st.expander("✏️ Editar venda existente"):
            ec1, ec2 = st.columns([1, 3])
            with ec1:
                edit_sale_id = st.number_input("ID da venda", min_value=1, step=1, key="edit_sale_id")
                load_sale    = st.button("Carregar", key="load_sale_btn")

            if load_sale:
                found = next((s for s in (sales_data or []) if s["id"] == edit_sale_id), None)
                if found:
                    st.session_state["edit_sale"] = found
                    st.success(f"Venda #{edit_sale_id} carregada.")
                else:
                    st.warning("ID não encontrado. Verifique o período selecionado.")

            if "edit_sale" in st.session_state:
                es = st.session_state["edit_sale"]
                with st.form("form_edit_venda"):
                    ee1, ee2 = st.columns(2)
                    with ee1:
                        es_date  = st.date_input("Data", value=date.fromisoformat(es["date"]), key="es_date")
                        es_store = st.selectbox("Loja", STORE_TUPLES, format_func=lambda s: s[1],
                                                index=next((i for i,(sid,_) in enumerate(STORE_TUPLES)
                                                            if sid==es["store_id"]), 0), key="es_store")
                    with ee2:
                        es_ch    = st.selectbox("Canal", CHANNELS,
                                                index=CHANNELS.index(es["channel"]) if es["channel"] in CHANNELS else 0,
                                                format_func=lambda c: {"pdv":"Balcão","ifood":"iFood","delivery":"Delivery"}.get(c,c),
                                                key="es_ch")
                        es_amt   = st.number_input("Valor (R$)", value=float(es["amount"]),
                                                   min_value=0.01, step=0.01, format="%.2f", key="es_amt")
                    save_sale = st.form_submit_button("💾 Salvar alterações", use_container_width=True)
                    if save_sale:
                        try:
                            r = httpx.put(f"{API_URL}/sales/{es['id']}", json={
                                "date": str(es_date), "store_id": es_store[0],
                                "store_name": es_store[1], "channel": es_ch, "amount": es_amt,
                            }, timeout=10)
                            r.raise_for_status()
                            st.success("Venda atualizada!")
                            del st.session_state["edit_sale"]
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

        # ── Excluir venda ──────────────────────────────────────────────────
        with st.expander("🗑️ Excluir venda"):
            del_id_s = st.number_input("ID da venda", min_value=1, step=1, key="del_sale")
            if st.button("Confirmar exclusão", key="btn_del_sale", type="primary"):
                try:
                    r = httpx.delete(f"{API_URL}/sales/{del_id_s}", timeout=10)
                    if r.status_code == 204:
                        st.success("Venda excluída.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Erro {r.status_code}")
                except Exception as e:
                    st.error(str(e))

    # ── SUB-TAB D: Gerenciar Custos ───────────────────────────────────────────
    with subtab_d:
        st.markdown('<div class="section-title">Custos do Período</div>', unsafe_allow_html=True)

        @st.cache_data(ttl=10)
        def fetch_costs_list(m, y):
            try:
                r = httpx.get(f"{API_URL}/costs/", params={"month": m, "year": y}, timeout=10)
                return r.json()
            except Exception:
                return []

        costs_data = fetch_costs_list(month, year)

        if not costs_data:
            st.info("Sem custos lançados para este período.")
        else:
            df_c2 = pd.DataFrame(costs_data)
            st.caption(f"**{len(df_c2)} registros** · Total: R$ {df_c2['amount'].sum():,.2f}")

            cf1, cf2, cf3 = st.columns(3)
            with cf1:
                cats_f  = ["Todas"] + sorted(df_c2["category"].dropna().unique().tolist())
                cat_sel = st.selectbox("Categoria", cats_f, key="cf_cat")
            with cf2:
                units_f  = ["Todas"] + sorted(df_c2["unit"].dropna().unique().tolist())
                unit_sel = st.selectbox("Unidade", units_f,
                                        format_func=lambda u: UNIT_LABELS.get(u,u) if u!="Todas" else "Todas",
                                        key="cf_unit")
            with cf3:
                orig_f  = ["Todas"] + sorted(df_c2["source"].dropna().unique().tolist())
                orig_sel = st.selectbox("Origem", orig_f, key="cf_orig")

            df_cv = df_c2.copy()
            if cat_sel  != "Todas": df_cv = df_cv[df_cv["category"] == cat_sel]
            if unit_sel != "Todas": df_cv = df_cv[df_cv["unit"] == unit_sel]
            if orig_sel != "Todas": df_cv = df_cv[df_cv["source"] == orig_sel]

            df_cv["unit_label"]  = df_cv["unit"].map(UNIT_LABELS).fillna(df_cv["unit"])
            df_cv["amount_fmt"]  = df_cv["amount"].apply(lambda v: f"R$ {v:,.2f}")
            df_cv["class_label"] = df_cv["category"].fillna("?") + " / " + df_cv["subcategory"].fillna("?")

            st.dataframe(
                df_cv[["id","date","description","amount_fmt","class_label","unit_label","source"]].rename(
                    columns={"id":"ID","date":"Data","description":"Descrição",
                             "amount_fmt":"Valor","class_label":"Classificação",
                             "unit_label":"Unidade","source":"Origem"}
                ),
                use_container_width=True, hide_index=True, height=280,
            )

        st.markdown("---")

        # ── Editar custo ───────────────────────────────────────────────────
        with st.expander("✏️ Editar custo existente"):
            ec1, ec2 = st.columns([1, 3])
            with ec1:
                edit_cost_id = st.number_input("ID do custo", min_value=1, step=1, key="edit_cost_id")
                load_cost    = st.button("Carregar", key="load_cost_btn")

            if load_cost:
                found_c = next((c for c in (costs_data or []) if c["id"] == edit_cost_id), None)
                if found_c:
                    st.session_state["edit_cost"] = found_c
                    st.success(f"Custo #{edit_cost_id} carregado.")
                else:
                    st.warning("ID não encontrado. Verifique o período selecionado.")

            if "edit_cost" in st.session_state:
                ec = st.session_state["edit_cost"]
                with st.form("form_edit_custo"):
                    ee1c, ee2c = st.columns(2)
                    with ee1c:
                        ec_date = st.date_input("Data", value=date.fromisoformat(ec["date"]), key="ec_date")
                        ec_desc = st.text_input("Descrição", value=ec["description"], key="ec_desc")
                        ec_amt  = st.number_input("Valor (R$)", value=float(ec["amount"]),
                                                  min_value=0.01, step=0.01, format="%.2f", key="ec_amt")
                    with ee2c:
                        ec_unit = st.selectbox("Unidade", UNITS_ALL,
                                               index=UNITS_ALL.index(ec["unit"]) if ec["unit"] in UNITS_ALL else 0,
                                               format_func=lambda u: UNIT_LABELS.get(u, u), key="ec_unit")
                        ec_cat  = st.selectbox("Categoria", CATS,
                                               index=CATS.index(ec["category"]) if ec.get("category") in CATS else 0,
                                               key="ec_cat")
                        ec_sc_opts = SUBCS.get(ec_cat, [])
                        ec_sc = st.selectbox("Subcategoria", ec_sc_opts if ec_sc_opts else ["—"],
                                             index=ec_sc_opts.index(ec["subcategory"]) if ec.get("subcategory") in ec_sc_opts else 0,
                                             key="ec_sc")
                    save_cost = st.form_submit_button("💾 Salvar alterações", use_container_width=True)
                    if save_cost:
                        try:
                            r = httpx.put(f"{API_URL}/costs/{ec['id']}", json={
                                "date": str(ec_date), "description": ec_desc,
                                "amount": ec_amt, "unit": ec_unit,
                                "category": ec_cat, "subcategory": ec_sc if ec_sc != "—" else "",
                            }, timeout=10)
                            r.raise_for_status()
                            st.success("Custo atualizado!")
                            del st.session_state["edit_cost"]
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

        # ── Reclassificar ──────────────────────────────────────────────────
        with st.expander("🏷️ Reclassificar custo (apenas categoria/unidade)"):
            rc1, rc2, rc3, rc4, rc5 = st.columns([1, 2, 2, 2, 1])
            with rc1:
                rc_id = st.number_input("ID", min_value=1, step=1, key="rc_id")
            with rc2:
                rc_cat = st.selectbox("Categoria", CATS, key="rc_cat")
            with rc3:
                rc_sc_opts = SUBCS.get(rc_cat, [])
                rc_subcat  = st.selectbox("Subcategoria", rc_sc_opts if rc_sc_opts else ["—"], key="rc_subcat")
            with rc4:
                rc_unit = st.selectbox("Unidade", UNITS_ALL,
                                       format_func=lambda u: UNIT_LABELS.get(u, u), key="rc_unit")
            with rc5:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Salvar", key="btn_rc"):
                    try:
                        r = httpx.patch(
                            f"{API_URL}/costs/{rc_id}/classify",
                            params={"category": rc_cat, "subcategory": rc_subcat, "unit": rc_unit},
                            timeout=10,
                        )
                        r.raise_for_status()
                        st.success(f"ID {rc_id} reclassificado.")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

        # ── Excluir custo ──────────────────────────────────────────────────
        with st.expander("🗑️ Excluir custo"):
            del_id_c = st.number_input("ID do custo", min_value=1, step=1, key="del_cost")
            if st.button("Confirmar exclusão", key="btn_del_cost", type="primary"):
                try:
                    r = httpx.delete(f"{API_URL}/costs/{del_id_c}", timeout=10)
                    if r.status_code == 204:
                        st.success("Custo excluído.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Erro {r.status_code}")
                except Exception as e:
                    st.error(str(e))

    # ── SUB-TAB E: Gerenciar Lojas ────────────────────────────────────────────
    with subtab_e:
        st.markdown('<div class="section-title">Lojas Cadastradas</div>', unsafe_allow_html=True)

        if all_stores:
            df_lojas = pd.DataFrame(all_stores)
            df_lojas["status"] = df_lojas["active"].map({True: "✅ Ativa", False: "⏸ Inativa"})
            df_lojas["store_name_full"] = df_lojas["store_id"].map(UNIT_LABELS).fillna(df_lojas["store_name"])
            st.dataframe(
                df_lojas[["store_id","store_name","status"]].rename(
                    columns={"store_id":"ID","store_name":"Nome","status":"Status"}
                ),
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("Nenhuma loja cadastrada.")

        st.markdown("---")

        # ── Adicionar loja ─────────────────────────────────────────────────
        with st.expander("➕ Adicionar nova loja"):
            with st.form("form_add_loja"):
                nl1, nl2 = st.columns(2)
                with nl1:
                    new_store_id   = st.text_input("ID da loja",
                                                    placeholder="Ex: loja_04",
                                                    help="Identificador único sem espaços. Ex: loja_04")
                with nl2:
                    new_store_name = st.text_input("Nome da loja",
                                                    placeholder="Ex: Loja Sul")
                add_loja = st.form_submit_button("✅ Cadastrar Loja", use_container_width=True)
                if add_loja:
                    if not new_store_id.strip() or not new_store_name.strip():
                        st.error("Preencha o ID e o nome da loja.")
                    elif " " in new_store_id:
                        st.error("O ID não pode ter espaços. Use underline: loja_04")
                    else:
                        try:
                            r = httpx.post(f"{API_URL}/stores/", json={
                                "store_id": new_store_id.strip().lower(),
                                "store_name": new_store_name.strip(),
                            }, timeout=10)
                            r.raise_for_status()
                            st.success(f"Loja **{new_store_name}** cadastrada com ID `{new_store_id}`!")
                            st.cache_data.clear()
                            st.rerun()
                        except httpx.HTTPStatusError as e:
                            st.error(e.response.json().get("detail", str(e)))
                        except Exception as e:
                            st.error(str(e))

        # ── Renomear loja ──────────────────────────────────────────────────
        with st.expander("✏️ Renomear loja"):
            store_ids = [s["store_id"] for s in all_stores]
            if store_ids:
                with st.form("form_rename_loja"):
                    rn1, rn2 = st.columns(2)
                    with rn1:
                        rename_id   = st.selectbox("Loja", store_ids,
                                                   format_func=lambda sid: f"{UNIT_LABELS.get(sid,sid)} ({sid})")
                    with rn2:
                        rename_name = st.text_input("Novo nome", placeholder="Ex: Loja Mercado Central")
                    save_rename = st.form_submit_button("💾 Salvar nome", use_container_width=True)
                    if save_rename:
                        if not rename_name.strip():
                            st.error("Informe o novo nome.")
                        else:
                            try:
                                r = httpx.put(f"{API_URL}/stores/{rename_id}", json={
                                    "store_id": rename_id,
                                    "store_name": rename_name.strip(),
                                }, timeout=10)
                                r.raise_for_status()
                                st.success(f"Loja renomeada para **{rename_name}**!")
                                st.cache_data.clear()
                                fetch_stores.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
            else:
                st.info("Nenhuma loja para renomear.")

        # ── Ativar / Desativar ─────────────────────────────────────────────
        with st.expander("⏸ Ativar / Desativar loja"):
            if all_stores:
                tog_id = st.selectbox("Loja", [s["store_id"] for s in all_stores],
                                      format_func=lambda sid: f"{UNIT_LABELS.get(sid,sid)} ({sid}) — "
                                                              f"{'Ativa' if next((s['active'] for s in all_stores if s['store_id']==sid), True) else 'Inativa'}",
                                      key="tog_store")
                tog_store_obj = next((s for s in all_stores if s["store_id"] == tog_id), None)
                btn_label = "⏸ Desativar" if tog_store_obj and tog_store_obj["active"] else "▶️ Ativar"
                if st.button(btn_label, key="btn_toggle_store"):
                    try:
                        r = httpx.patch(f"{API_URL}/stores/{tog_id}/toggle", timeout=10)
                        r.raise_for_status()
                        novo = r.json()["active"]
                        st.success(f"Loja {'ativada' if novo else 'desativada'}.")
                        st.cache_data.clear()
                        fetch_stores.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))


    # ── SUB-TAB F: Segurança dos dados ───────────────────────────────────────
    with subtab_f:
        st.markdown('<div class="section-title">Segurança e Backup dos Dados</div>',
                    unsafe_allow_html=True)

        # Localização do banco
        st.markdown("""
        <div style="background:rgba(0,200,150,0.1);border:1px solid #00C896;border-radius:10px;padding:16px;margin-bottom:16px;">
            <strong style="color:#00C896;">✅ Seus dados estão seguros</strong><br>
            <span style="color:#ccc;font-size:0.9rem;">
            O banco de dados fica salvo em:<br>
            <code style="color:#C9B8FF;">Kinga Finance AI / data / kinga_finance.db</code><br><br>
            Um backup automático é criado toda vez que o sistema é iniciado.
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Backup manual
        sb1, sb2 = st.columns(2)
        with sb1:
            st.markdown("**Fazer backup agora**")
            if st.button("💾 Criar Backup Manual", use_container_width=True):
                try:
                    r = httpx.post(f"{API_URL}/backup", timeout=10)
                    r.raise_for_status()
                    resp = r.json()
                    st.success(f"Backup criado: `{resp.get('arquivo', '')}`")
                except Exception as e:
                    st.error(str(e))

        with sb2:
            st.markdown("**Exportar dados (CSV)**")
            ec1, ec2 = st.columns(2)
            with ec1:
                if st.button("📥 Exportar Vendas", use_container_width=True):
                    st.markdown(f'<a href="{API_URL}/export/sales" target="_blank" '
                                f'style="color:#C9B8FF;">→ Clique aqui para baixar vendas_kinga.csv</a>',
                                unsafe_allow_html=True)
            with ec2:
                if st.button("📥 Exportar Custos", use_container_width=True):
                    st.markdown(f'<a href="{API_URL}/export/costs" target="_blank" '
                                f'style="color:#C9B8FF;">→ Clique aqui para baixar custos_kinga.csv</a>',
                                unsafe_allow_html=True)

        st.markdown("---")

        # Lista de backups
        st.markdown("**Backups disponíveis**")
        try:
            r = httpx.get(f"{API_URL}/backup/list", timeout=5)
            bkps = r.json().get("backups", [])
            if bkps:
                df_bkp = pd.DataFrame(bkps)
                df_bkp.columns = ["Arquivo", "Tamanho (KB)", "Data"]
                st.dataframe(df_bkp, use_container_width=True, hide_index=True)
                st.caption(f"{len(bkps)} backup(s) disponíveis · Máximo 30 mantidos automaticamente.")
            else:
                st.info("Nenhum backup ainda. Será criado na próxima vez que o sistema iniciar.")
        except Exception:
            st.warning("Não foi possível listar backups.")




st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#4A3570;font-size:0.78rem;padding:8px;'>"
    "Kinga Finance AI · Kinga Açaí Frozen · 2026"
    "</div>",
    unsafe_allow_html=True,
)
