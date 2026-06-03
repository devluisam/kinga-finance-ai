"""
Kinga Finance AI — Agente Principal
Orquestra todos os módulos e gera o relatório completo em linguagem natural.
"""
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.modules import billing, costs, results, factory as factory_mod, alerts as alerts_mod
from app.models.store import Store

# Fallback caso a tabela de lojas esteja vazia
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
    narrative: str = field(default="")


def run_report(db: Session, month: int, year: int) -> FinancialReport:
    # Módulo 1 — Faturamento
    fat_total = billing.total_revenue(db, month, year)
    fat_por_loja = billing.revenue_by_store(db, month, year)
    var_fat = billing.revenue_growth(db, month, year)
    weekly = billing.weekly_revenue(db, month, year)

    # Módulo 2 — Custos
    custo_total = costs.total_costs(db, month, year)
    custo_cat = costs.costs_by_category(db, month, year)
    custo_subcat = costs.costs_by_subcategory(db, month, year)
    custo_unit = costs.costs_by_unit(db, month, year)
    var_custo = costs.costs_growth(db, month, year)

    # Módulo 4/5 — Resultado
    op_result = results.compute_result(fat_total, custo_total, var_fat, var_custo)

    # Módulo 6 — Por loja
    store_map  = _get_store_map(db)
    store_list = results.compute_store_results(fat_por_loja, custo_unit, store_map)

    # Módulo 7 — Fábrica
    fab = factory_mod.factory_report(db, month, year, fat_total)

    # Módulo 9 — Alertas
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    prev_store = billing.revenue_by_store(db, prev_month, prev_year)
    alert_list = alerts_mod.generate_alerts(op_result, store_list, fab, prev_store or None)

    # Narrativa do agente
    narrative = _build_narrative(op_result, store_list, fab, alert_list)

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
        narrative=narrative,
    )


def _build_narrative(
    op: results.OperationalResult,
    stores: list[results.StoreResult],
    fab: factory_mod.FactoryReport,
    alerts: list[alerts_mod.Alert],
) -> str:
    lines: list[str] = []

    # Abertura
    status_emoji = "✅" if op.status == "LUCRO" else ("❌" if op.status == "PREJUÍZO" else "⚖️")
    lines.append(
        f"{status_emoji} **Resultado do período: {op.status}**\n"
        f"Faturamento de R$ {op.faturamento:,.2f} com custos de R$ {op.custos:,.2f}. "
        f"Resultado: R$ {op.resultado:,.2f} ({op.margem_pct:.1f}% de margem)."
    )

    # Evolução
    if op.variacao_faturamento != 0:
        sinal = "cresceu" if op.variacao_faturamento > 0 else "caiu"
        lines.append(
            f"O faturamento {sinal} {abs(op.variacao_faturamento):.1f}% em relação ao mês anterior."
        )

    # Diagnóstico de custos vs vendas
    if op.variacao_custos > op.variacao_faturamento + 3:
        lines.append(
            f"⚠️ Atenção: os custos cresceram {op.variacao_custos:.1f}% enquanto as vendas "
            f"cresceram apenas {op.variacao_faturamento:.1f}%. Isso comprime sua margem."
        )

    # Melhor e pior loja
    if stores:
        melhor = max(stores, key=lambda s: s.margem_pct)
        pior = min(stores, key=lambda s: s.margem_pct)
        lines.append(
            f"📊 Melhor unidade: **{melhor.store_name}** ({melhor.margem_pct:.1f}% de margem). "
            f"Pior unidade: **{pior.store_name}** ({pior.margem_pct:.1f}% de margem)."
        )

    # Fábrica
    if fab.custos_totais > 0:
        lines.append(
            f"🏭 A fábrica representou {fab.pct_faturamento:.1f}% do faturamento total "
            f"(R$ {fab.custos_totais:,.2f} em custos). "
            f"Folha da fábrica: {fab.peso_folha:.1f}% dos custos de produção."
        )

    # Alertas prioritários
    danger_alerts = [a for a in alerts if a.level == "danger"]
    if danger_alerts:
        lines.append("\n🚨 **Ações urgentes necessárias:**")
        for a in danger_alerts[:3]:
            lines.append(f"• {a.title}: {a.suggestion}")

    return "\n\n".join(lines)
