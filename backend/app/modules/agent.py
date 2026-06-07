"""
Kinga Finance AI — Agente Principal
Orquestra todos os módulos e gera o relatório completo em linguagem natural.
"""
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.modules import billing, costs, results, factory as factory_mod, alerts as alerts_mod
from app.modules.forecast import project_month, ForecastReport
from app.modules.health import compute_health, HealthScore
from app.models.store import Store

_DEFAULT_STORE_MAP = {
    "loja_01": "Loja Centro",
    "loja_02": "Loja Shopping",
    "loja_03": "Loja Norte",
    "fabrica": "Fábrica",
    "admin": "Administrativo",
}


def _get_store_map(db: Session) -> dict[str, str]:
    rows = db.query(Store).filter(Store.active.is_(True)).all()
    if not rows:
        return _DEFAULT_STORE_MAP
    return {s.store_id: s.store_name for s in rows}


@dataclass
class FinancialReport:
    month: int
    year: int
    result: results.OperationalResult
    store_results: list[results.StoreResult]
    factory: factory_mod.FactoryReport
    costs_by_category: dict[str, float]
    costs_by_subcategory: list[dict]
    weekly_revenue: list[dict]
    alerts: list[alerts_mod.Alert]
    forecast: ForecastReport
    health: HealthScore
    channel_revenue: dict[str, float]
    narrative: str = field(default="")


def run_report(db: Session, month: int, year: int) -> FinancialReport:
    # ── Módulo 1: Faturamento ─────────────────────────────────────────────────
    fat_total = billing.total_revenue(db, month, year)
    fat_por_loja = billing.revenue_by_store(db, month, year)
    fat_por_canal = billing.revenue_by_channel(db, month, year)
    var_fat = billing.revenue_growth(db, month, year)
    weekly = billing.weekly_revenue(db, month, year)

    # ── Módulo 2: Custos ──────────────────────────────────────────────────────
    custo_total = costs.total_costs(db, month, year)
    custo_cat = costs.costs_by_category(db, month, year)
    custo_subcat = costs.costs_by_subcategory(db, month, year)
    custo_unit = costs.costs_by_unit(db, month, year)
    var_custo = costs.costs_growth(db, month, year)

    # Mês anterior — para alertas e comparações
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    fat_mes_anterior = billing.total_revenue(db, prev_month, prev_year)
    prev_store = billing.revenue_by_store(db, prev_month, prev_year) or {}
    prev_costs_cat = costs.costs_by_category(db, prev_month, prev_year) or {}

    # ── Módulo 4/5: Resultado operacional ────────────────────────────────────
    op_result = results.compute_result(fat_total, custo_total, var_fat, var_custo)

    # ── Por loja ──────────────────────────────────────────────────────────────
    store_map = _get_store_map(db)
    store_list = results.compute_store_results(fat_por_loja, custo_unit, store_map)

    # ── Módulo 7: Fábrica ─────────────────────────────────────────────────────
    fab = factory_mod.factory_report(db, month, year, fat_total)

    # ── Projeção de fechamento ────────────────────────────────────────────────
    forecast = project_month(db, month, year, fat_mes_anterior=fat_mes_anterior)

    # ── Score de saúde financeira ─────────────────────────────────────────────
    stores_negativas = sum(1 for s in store_list if s.margem_pct < 0)
    health = compute_health(op_result, len(store_list), stores_negativas)

    # ── Anomalias de custo (categoria cresceu > 30%) ─────────────────────────
    cost_anomalies: list[alerts_mod.Alert] = []
    for cat, val_atual in custo_cat.items():
        val_prev = prev_costs_cat.get(cat, 0.0)
        if val_prev > 0:
            var_cat = (val_atual - val_prev) / val_prev * 100
            if var_cat > 30:
                cost_anomalies.append(alerts_mod.Alert(
                    level="warning",
                    title=f"Anomalia em {cat}",
                    message=(
                        f"Custo de '{cat}' cresceu {var_cat:.1f}% vs mês anterior "
                        f"(R$ {val_prev:,.2f} → R$ {val_atual:,.2f})."
                    ),
                    suggestion=f"Investigue o que elevou os gastos em '{cat}' este mês.",
                ))

    # ── Módulo 9: Alertas ────────────────────────────────────────────────────
    alert_list = alerts_mod.generate_alerts(
        op_result,
        store_list,
        fab,
        prev_store_revenues=prev_store or None,
        channel_revenues=fat_por_canal or None,
        fat_projetado=forecast.fat_projetado,
        fat_mes_anterior=fat_mes_anterior,
    )
    alert_list.extend(cost_anomalies)

    # ── Narrativa ─────────────────────────────────────────────────────────────
    narrative = _build_narrative(op_result, store_list, fab, alert_list, forecast, health, fat_por_canal)

    return FinancialReport(
        month=month,
        year=year,
        result=op_result,
        store_results=store_list,
        factory=fab,
        costs_by_category=custo_cat,
        costs_by_subcategory=custo_subcat,
        weekly_revenue=weekly,
        alerts=alert_list,
        forecast=forecast,
        health=health,
        channel_revenue=fat_por_canal,
        narrative=narrative,
    )


def _build_narrative(
    op: results.OperationalResult,
    stores: list[results.StoreResult],
    fab: factory_mod.FactoryReport,
    alerts: list[alerts_mod.Alert],
    forecast: ForecastReport,
    health: HealthScore,
    channels: dict[str, float],
) -> str:
    lines: list[str] = []

    # Abertura com score de saúde
    status_emoji = "✅" if op.status == "LUCRO" else ("❌" if op.status == "PREJUÍZO" else "⚖️")
    lines.append(
        f"{status_emoji} **{op.status}** — Score de Saúde: {health.score:.0f}/100 ({health.grade})\n"
        f"Faturamento de R$ {op.faturamento:,.2f} com custos de R$ {op.custos:,.2f}. "
        f"Resultado: R$ {op.resultado:,.2f} ({op.margem_pct:.1f}% de margem)."
    )

    # Evolução vs mês anterior
    if op.variacao_faturamento != 0:
        sinal = "cresceu" if op.variacao_faturamento > 0 else "caiu"
        lines.append(
            f"O faturamento {sinal} {abs(op.variacao_faturamento):.1f}% em relação ao mês anterior."
        )

    # Projeção (só para mês corrente com dias restantes)
    if forecast.dias_restantes > 0 and forecast.fat_projetado > 0:
        tend_label = {"ACIMA": "acima", "ABAIXO": "abaixo", "NO_RITMO": "no ritmo"}.get(
            forecast.tendencia, ""
        )
        lines.append(
            f"📅 Projeção de fechamento: R$ {forecast.fat_projetado:,.2f} "
            + (f"({tend_label} do mês anterior)." if tend_label else ".")
            + f" Restam {forecast.dias_restantes} dias com ritmo de R$ {forecast.fat_diario:,.2f}/dia."
        )

    # Diagnóstico custos vs vendas
    diff = op.variacao_custos - op.variacao_faturamento
    if diff > 5:
        lines.append(
            f"⚠️ Atenção: custos cresceram {op.variacao_custos:.1f}% enquanto vendas "
            f"cresceram {op.variacao_faturamento:.1f}%. Isso comprime a margem."
        )

    # Canal de maior participação
    if channels:
        total_ch = sum(channels.values())
        ch_labels = {"pdv": "Balcão", "ifood": "iFood", "delivery": "Delivery"}
        top_ch = max(channels, key=channels.get)
        if total_ch > 0:
            pct_top = channels[top_ch] / total_ch * 100
            lines.append(
                f"Canal principal: **{ch_labels.get(top_ch, top_ch)}** "
                f"com {pct_top:.1f}% das receitas."
            )

    # Melhor e pior loja
    if stores:
        melhor = max(stores, key=lambda s: s.margem_pct)
        pior = min(stores, key=lambda s: s.margem_pct)
        lines.append(
            f"📊 Melhor unidade: **{melhor.store_name}** ({melhor.margem_pct:.1f}% de margem). "
            f"Pior: **{pior.store_name}** ({pior.margem_pct:.1f}%)."
        )

    # Fábrica
    if fab.custos_totais > 0:
        lines.append(
            f"🏭 Fábrica: R$ {fab.custos_totais:,.2f} ({fab.pct_faturamento:.1f}% do faturamento). "
            f"Folha: {fab.peso_folha:.1f}% dos custos de produção."
        )

    # Alertas urgentes
    danger_alerts = [a for a in alerts if a.level == "danger"]
    if danger_alerts:
        lines.append("\n🚨 **Ações urgentes:**")
        for a in danger_alerts[:3]:
            lines.append(f"• {a.title}: {a.suggestion}")

    return "\n\n".join(lines)
