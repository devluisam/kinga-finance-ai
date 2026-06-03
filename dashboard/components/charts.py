import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

PURPLE = "#6C3FC5"
PINK   = "#E91E8C"
GREEN  = "#00C896"
RED    = "#FF4B4B"
YELLOW = "#FFB300"
BG     = "#0F0A1A"
CARD   = "#1A1033"
TEXT   = "#F0E6FF"

PALETTE = [PURPLE, PINK, GREEN, "#3498DB", YELLOW, RED, "#9B59B6", "#1ABC9C"]

LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT, family="Inter, sans-serif"),
    margin=dict(t=50, b=30, l=20, r=20),
)


def _safe_df(store_results: list[dict], required_cols: list[str]) -> pd.DataFrame:
    if not store_results:
        return pd.DataFrame(columns=required_cols)
    df = pd.DataFrame(store_results)
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0
    return df


def gauge_chart(value: float, title: str) -> go.Figure:
    if value >= 15:
        color = GREEN
    elif value >= 0:
        color = YELLOW
    else:
        color = RED

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%", "font": {"size": 40, "color": color}},
        title={"text": title, "font": {"size": 14, "color": TEXT}},
        gauge={
            "axis": {"range": [-20, 50], "tickcolor": TEXT, "tickfont": {"color": TEXT}},
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": CARD,
            "borderwidth": 0,
            "steps": [
                {"range": [-20, 0],  "color": "rgba(255,75,75,0.15)"},
                {"range": [0, 15],   "color": "rgba(255,179,0,0.15)"},
                {"range": [15, 50],  "color": "rgba(0,200,150,0.15)"},
            ],
            "threshold": {
                "line": {"color": GREEN, "width": 3},
                "thickness": 0.8,
                "value": 15,
            },
        },
    ))
    fig.update_layout(**LAYOUT_BASE, height=240)
    return fig


def donut_chart(labels: list, values: list, title: str) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=PALETTE, line=dict(color=BG, width=2)),
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f} (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=title, font=dict(size=14, color=TEXT)),
        showlegend=True,
        legend=dict(font=dict(color=TEXT, size=11), orientation="v"),
        height=280,
    )
    return fig


def bar_store_comparison(store_results: list[dict]) -> go.Figure:
    df = _safe_df(store_results, ["store_name", "faturamento", "custos"])
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Faturamento",
        x=df["store_name"],
        y=df["faturamento"],
        marker=dict(color=PURPLE, line=dict(width=0)),
        text=df["faturamento"].apply(lambda v: f"R$ {v:,.0f}"),
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
    ))
    fig.add_trace(go.Bar(
        name="Custos",
        x=df["store_name"],
        y=df["custos"],
        marker=dict(color=PINK, line=dict(width=0)),
        text=df["custos"].apply(lambda v: f"R$ {v:,.0f}"),
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        barmode="group",
        title=dict(text="Faturamento vs Custos por Loja", font=dict(size=14, color=TEXT)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickprefix="R$ "),
        xaxis=dict(tickfont=dict(color=TEXT)),
        legend=dict(font=dict(color=TEXT), orientation="h", y=1.1),
        height=320,
    )
    return fig


def margin_bar(store_results: list[dict]) -> go.Figure:
    df = _safe_df(store_results, ["store_name", "margem_pct"])
    df = df.sort_values("margem_pct")
    colors = [GREEN if m >= 15 else (YELLOW if m >= 0 else RED) for m in df["margem_pct"]]
    fig = go.Figure(go.Bar(
        x=df["margem_pct"],
        y=df["store_name"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=df["margem_pct"].apply(lambda v: f"  {v:.1f}%"),
        textposition="outside",
        textfont=dict(color=TEXT, size=12),
    ))
    fig.add_vline(x=15, line_dash="dot", line_color=GREEN, line_width=2,
                  annotation_text="Meta 15%", annotation_font_color=GREEN)
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="Margem por Unidade", font=dict(size=14, color=TEXT)),
        xaxis=dict(ticksuffix="%", gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color=TEXT)),
        yaxis=dict(tickfont=dict(color=TEXT)),
        height=280,
    )
    return fig


def weekly_line(weekly: list[dict]) -> go.Figure:
    fig = go.Figure()
    if not weekly:
        fig.update_layout(**LAYOUT_BASE, height=240,
                          title=dict(text="Evolução Semanal", font=dict(size=14)))
        return fig
    df = pd.DataFrame(weekly)
    fig.add_trace(go.Scatter(
        x=df["semana"].apply(lambda w: f"Sem. {w}"),
        y=df["faturamento"],
        mode="lines+markers",
        line=dict(color=PURPLE, width=3),
        marker=dict(color=PINK, size=8, line=dict(color=TEXT, width=1)),
        fill="tozeroy",
        fillcolor="rgba(108,63,197,0.15)",
        hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="Faturamento Semanal", font=dict(size=14, color=TEXT)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickprefix="R$ "),
        xaxis=dict(tickfont=dict(color=TEXT)),
        height=240,
    )
    return fig


def factory_bar(factory: dict) -> go.Figure:
    labels = ["Mat. Prima", "Folha", "Energia", "Frete", "Outros"]
    values = [
        factory.get("materia_prima", 0),
        factory.get("folha", 0),
        factory.get("energia", 0),
        factory.get("frete", 0),
        factory.get("outros", 0),
    ]
    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker=dict(color=PALETTE[:5], line=dict(width=0)),
        text=[f"R$ {v:,.0f}" for v in values],
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="Composição de Custos da Fábrica", font=dict(size=14, color=TEXT)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickprefix="R$ "),
        xaxis=dict(tickfont=dict(color=TEXT)),
        height=280,
    )
    return fig


def result_waterfall(faturamento: float, custos: float, resultado: float) -> go.Figure:
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "total"],
        x=["Faturamento", "Custos", "Resultado"],
        y=[faturamento, -custos, resultado],
        text=[f"R$ {faturamento:,.0f}", f"- R$ {custos:,.0f}", f"R$ {resultado:,.0f}"],
        textposition="outside",
        textfont=dict(color=TEXT),
        connector={"line": {"color": "rgba(255,255,255,0.2)"}},
        increasing={"marker": {"color": GREEN}},
        decreasing={"marker": {"color": RED}},
        totals={"marker": {"color": PURPLE}},
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="Demonstrativo de Resultado", font=dict(size=14, color=TEXT)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickprefix="R$ "),
        height=300,
    )
    return fig
