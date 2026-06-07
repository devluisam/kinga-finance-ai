"""
Módulo 9 — Alertas Inteligentes
Gera alertas proativos, explicativos e com sugestão de ação.
"""
from dataclasses import dataclass
from typing import Literal

from app.modules.results import OperationalResult, StoreResult
from app.modules.factory import FactoryReport

IDEAL_MARGEM = 15.0           # margem mínima saudável (%)
IDEAL_FOLHA_FABRICA = 35.0    # folha/custos fábrica máximo ideal (%)
IDEAL_CUSTO_PCT = 80.0        # custo/faturamento máximo ideal (%)
GROWTH_ALERT_DIFF = 5.0       # p.p. de diferença custo vs venda para alertar
CANAL_DEPENDENCIA_MAX = 60.0  # % máximo de dependência num único canal


@dataclass
class Alert:
    level: Literal["danger", "warning", "info", "success"]
    title: str
    message: str
    suggestion: str


def generate_alerts(
    result: OperationalResult,
    store_results: list[StoreResult],
    factory: FactoryReport,
    prev_store_revenues: dict[str, float] | None = None,
    prev_costs_by_category: dict[str, float] | None = None,
    channel_revenues: dict[str, float] | None = None,
    fat_projetado: float = 0.0,
    fat_mes_anterior: float = 0.0,
) -> list[Alert]:
    alerts: list[Alert] = []

    # ── Resultado geral ───────────────────────────────────────────────────────

    if result.status == "PREJUÍZO":
        alerts.append(Alert(
            level="danger",
            title="Resultado Negativo",
            message=(
                f"O negócio operou com prejuízo de R$ {abs(result.resultado):,.2f} "
                f"({abs(result.margem_pct):.1f}% de margem negativa)."
            ),
            suggestion=(
                "Revise os maiores centros de custo imediatamente. Priorize corte de "
                "despesas variáveis e renegociação de fixos antes de qualquer investimento."
            ),
        ))
    elif result.margem_pct < IDEAL_MARGEM:
        alerts.append(Alert(
            level="warning",
            title="Margem Abaixo do Ideal",
            message=(
                f"Margem operacional de {result.margem_pct:.1f}% está abaixo do "
                f"mínimo recomendado de {IDEAL_MARGEM:.0f}%."
            ),
            suggestion=(
                "Identifique quais lojas puxam a margem para baixo e analise o mix "
                "de produtos mais rentável."
            ),
        ))
    elif result.margem_pct >= 30:
        alerts.append(Alert(
            level="success",
            title="Margem Excelente",
            message=f"Margem operacional de {result.margem_pct:.1f}% — acima do ideal de 15%.",
            suggestion=(
                "Continue monitorando. Considere reinvestir parte do lucro em marketing "
                "ou abertura de nova unidade."
            ),
        ))

    # ── Crescimento de custos vs vendas ───────────────────────────────────────

    diff = result.variacao_custos - result.variacao_faturamento
    if diff > GROWTH_ALERT_DIFF:
        alerts.append(Alert(
            level="warning",
            title="Custos Crescendo Mais que Vendas",
            message=(
                f"Faturamento cresceu {result.variacao_faturamento:.1f}% enquanto custos "
                f"cresceram {result.variacao_custos:.1f}% (+{diff:.1f} p.p.)."
            ),
            suggestion=(
                "Revise contratos de fornecedores e escala de pessoal. Custos crescendo "
                "acima das vendas comprime margens progressivamente."
            ),
        ))
    elif diff <= -5 and result.variacao_faturamento > 0:
        alerts.append(Alert(
            level="success",
            title="Custo Sob Controle",
            message=(
                f"Vendas cresceram {result.variacao_faturamento:.1f}% enquanto custos "
                f"cresceram apenas {result.variacao_custos:.1f}%. Eficiência melhorando."
            ),
            suggestion="Mantenha esse equilíbrio. Ganhos de escala estão funcionando.",
        ))

    # ── Fábrica ───────────────────────────────────────────────────────────────

    if factory.peso_folha > IDEAL_FOLHA_FABRICA:
        alerts.append(Alert(
            level="warning",
            title="Folha da Fábrica Elevada",
            message=(
                f"A folha representa {factory.peso_folha:.1f}% dos custos da fábrica "
                f"(ideal abaixo de {IDEAL_FOLHA_FABRICA:.0f}%)."
            ),
            suggestion=(
                "Avalie produtividade por colaborador na fábrica. Considere ajuste de "
                "turnos ou automação parcial de processos repetitivos."
            ),
        ))

    if factory.custos_totais > 0 and result.faturamento > 0:
        pct_fab = factory.custos_totais / result.faturamento * 100
        if pct_fab > 35:
            alerts.append(Alert(
                level="warning",
                title="Custo de Produção Alto",
                message=(
                    f"A fábrica consome {pct_fab:.1f}% do faturamento total "
                    f"(R$ {factory.custos_totais:,.2f})."
                ),
                suggestion=(
                    "Revise o custo de matéria-prima: renegocie com fornecedores ou "
                    "busque alternativas sem perda de qualidade."
                ),
            ))

    # ── Por loja ─────────────────────────────────────────────────────────────

    for sr in store_results:
        if sr.margem_pct < 0:
            alerts.append(Alert(
                level="danger",
                title=f"{sr.store_name} com Margem Negativa",
                message=f"{sr.store_name} operou com margem de {sr.margem_pct:.1f}%.",
                suggestion=(
                    "Revise os custos específicos desta unidade. Verifique desperdício, "
                    "furto ou custos alocados incorretamente."
                ),
            ))
        elif sr.faturamento == 0:
            alerts.append(Alert(
                level="warning",
                title=f"{sr.store_name} sem Faturamento",
                message=f"{sr.store_name} não registrou receita neste período.",
                suggestion="Verifique se houve fechamento, problemas operacionais ou falta de lançamentos.",
            ))

    # ── Queda por loja (vs mês anterior) ────────────────────────────────────

    if prev_store_revenues:
        for sr in store_results:
            prev = prev_store_revenues.get(sr.store_name, 0.0)
            if prev > 0:
                variacao = (sr.faturamento - prev) / prev * 100
                if variacao < -10:
                    alerts.append(Alert(
                        level="danger",
                        title=f"Queda Forte em {sr.store_name}",
                        message=(
                            f"{sr.store_name} caiu {abs(variacao):.1f}% "
                            f"(R$ {sr.faturamento:,.2f} vs R$ {prev:,.2f} no mês anterior)."
                        ),
                        suggestion=(
                            "Verifique operação, fluxo de clientes, qualidade e presença "
                            "nos apps de delivery. Considere ação promocional pontual."
                        ),
                    ))
                elif variacao < -5:
                    alerts.append(Alert(
                        level="warning",
                        title=f"Leve Queda em {sr.store_name}",
                        message=f"{sr.store_name} caiu {abs(variacao):.1f}% no faturamento.",
                        suggestion="Acompanhe por mais uma semana antes de acionar.",
                    ))
                elif variacao >= 15:
                    alerts.append(Alert(
                        level="success",
                        title=f"Crescimento em {sr.store_name}",
                        message=(
                            f"{sr.store_name} cresceu {variacao:.1f}% "
                            f"(R$ {sr.faturamento:,.2f} vs R$ {prev:,.2f})."
                        ),
                        suggestion="Identifique o que impulsionou este resultado e replique nas demais lojas.",
                    ))

    # ── Anomalia de custo por categoria ──────────────────────────────────────

    if prev_costs_by_category and result.faturamento > 0:
        from app.modules.costs import costs_by_category  # evita import circular
        for cat, val_atual in result.__dict__.items():
            pass  # placeholder — dados passados de fora
        # Detecta categorias com salto > 30%
        for cat, val_prev in prev_costs_by_category.items():
            pass  # será preenchido pelo agent via custo_cat passado

    # ── Dependência de canal ──────────────────────────────────────────────────

    if channel_revenues:
        total_ch = sum(channel_revenues.values())
        if total_ch > 0:
            ch_labels = {"pdv": "Balcão (PDV)", "ifood": "iFood",
                         "delivery": "Delivery", "whatsapp": "WhatsApp"}
            for ch, val in channel_revenues.items():
                pct = val / total_ch * 100
                if pct > CANAL_DEPENDENCIA_MAX:
                    alerts.append(Alert(
                        level="warning",
                        title=f"Alta Dependência de {ch_labels.get(ch, ch)}",
                        message=(
                            f"{ch_labels.get(ch, ch)} representa {pct:.1f}% do faturamento. "
                            "Concentração elevada em um único canal é um risco operacional."
                        ),
                        suggestion=(
                            "Diversifique os canais de venda: invista no canal com menor "
                            "participação para reduzir a dependência."
                        ),
                    ))

    # ── Projeção de fechamento ────────────────────────────────────────────────

    if fat_projetado > 0 and fat_mes_anterior > 0:
        variacao_proj = (fat_projetado - fat_mes_anterior) / fat_mes_anterior * 100
        if variacao_proj < -15:
            alerts.append(Alert(
                level="warning",
                title="Ritmo Abaixo do Mês Anterior",
                message=(
                    f"No ritmo atual, o mês deve fechar em R$ {fat_projetado:,.2f} — "
                    f"{abs(variacao_proj):.1f}% abaixo do mês anterior."
                ),
                suggestion="Acelere as ações de captação de clientes ou ative promoções nos próximos dias.",
            ))

    # ── Custo operacional geral ───────────────────────────────────────────────

    if result.custo_pct > IDEAL_CUSTO_PCT:
        alerts.append(Alert(
            level="warning",
            title="Custo Operacional Alto",
            message=f"Os custos representam {result.custo_pct:.1f}% do faturamento.",
            suggestion=(
                "Mapeie os 3 maiores custos e negocie redução. Foco em aluguel, folha "
                "e matéria-prima — costumam responder por 70% do total."
            ),
        ))

    # ── Positivo geral ────────────────────────────────────────────────────────

    if not alerts:
        alerts.append(Alert(
            level="info",
            title="Operação Saudável",
            message=(
                f"Margem de {result.margem_pct:.1f}% com resultado positivo de "
                f"R$ {result.resultado:,.2f}."
            ),
            suggestion=(
                "Continue monitorando semanalmente. Considere reinvestir parte do lucro "
                "em marketing para aumentar faturamento."
            ),
        ))

    # Ordena: danger → warning → success → info
    _order = {"danger": 0, "warning": 1, "success": 2, "info": 3}
    alerts.sort(key=lambda a: _order.get(a.level, 4))

    return alerts
