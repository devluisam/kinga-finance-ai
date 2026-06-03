"""
Módulo 9 — Alertas Inteligentes
Gera alertas proativos, explicativos e com sugestão de ação.
"""
from dataclasses import dataclass
from typing import Literal

from app.modules.results import OperationalResult, StoreResult
from app.modules.factory import FactoryReport

IDEAL_MARGEM = 15.0          # margem mínima saudável (%)
IDEAL_FOLHA_FABRICA = 35.0   # folha/custos fábrica máximo ideal (%)
IDEAL_CUSTO_PCT = 80.0       # custo/faturamento máximo ideal (%)
GROWTH_ALERT_DIFF = 5.0      # diferença entre crescimento de custo e venda


@dataclass
class Alert:
    level: Literal["danger", "warning", "info"]
    title: str
    message: str
    suggestion: str


def generate_alerts(
    result: OperationalResult,
    store_results: list[StoreResult],
    factory: FactoryReport,
    prev_store_revenues: dict[str, float] | None = None,
) -> list[Alert]:
    alerts: list[Alert] = []

    # 1. Margem negativa
    if result.status == "PREJUÍZO":
        alerts.append(Alert(
            level="danger",
            title="Resultado Negativo",
            message=f"O negócio operou com prejuízo de R$ {abs(result.resultado):,.2f} "
                    f"({abs(result.margem_pct):.1f}% de margem negativa).",
            suggestion="Revise os maiores centros de custo. Priorize corte de despesas variáveis "
                       "e renegociação de fixos antes de qualquer investimento.",
        ))

    # 2. Margem abaixo do ideal
    elif result.margem_pct < IDEAL_MARGEM:
        alerts.append(Alert(
            level="warning",
            title="Margem Abaixo do Ideal",
            message=f"Margem operacional de {result.margem_pct:.1f}% está abaixo do mínimo "
                    f"recomendado de {IDEAL_MARGEM:.0f}%.",
            suggestion="Identifique quais lojas puxam a margem para baixo e analise o mix de "
                       "produtos mais rentável.",
        ))

    # 3. Custos cresceram mais que vendas
    diff = result.variacao_custos - result.variacao_faturamento
    if diff > GROWTH_ALERT_DIFF:
        alerts.append(Alert(
            level="warning",
            title="Custos Crescendo Mais que Vendas",
            message=f"Faturamento cresceu {result.variacao_faturamento:.1f}% enquanto custos "
                    f"cresceram {result.variacao_custos:.1f}% (+{diff:.1f} p.p. de diferença).",
            suggestion="Revise contratos de fornecedores e escala de pessoal. Custos crescendo "
                       "acima das vendas comprime margens progressivamente.",
        ))

    # 4. Folha da fábrica acima do ideal
    if factory.peso_folha > IDEAL_FOLHA_FABRICA:
        alerts.append(Alert(
            level="warning",
            title="Folha da Fábrica Elevada",
            message=f"A folha representa {factory.peso_folha:.1f}% dos custos da fábrica "
                    f"(ideal abaixo de {IDEAL_FOLHA_FABRICA:.0f}%).",
            suggestion="Avalie a produtividade por colaborador da fábrica. Considere ajuste "
                       "de turnos ou automação parcial de processos repetitivos.",
        ))

    # 5. Queda de faturamento por loja
    if prev_store_revenues:
        for sr in store_results:
            prev = prev_store_revenues.get(sr.store_name, 0.0)
            if prev > 0:
                variacao = (sr.faturamento - prev) / prev * 100
                if variacao < -10:
                    alerts.append(Alert(
                        level="danger",
                        title=f"Queda em {sr.store_name}",
                        message=f"{sr.store_name} teve queda de {abs(variacao):.1f}% no faturamento "
                                f"(R$ {sr.faturamento:,.2f} vs R$ {prev:,.2f} anterior).",
                        suggestion="Verifique operação, fluxo de clientes, qualidade e presença "
                                   "nos apps de delivery. Considere ação promocional pontual.",
                    ))
                elif variacao < -5:
                    alerts.append(Alert(
                        level="warning",
                        title=f"Leve Queda em {sr.store_name}",
                        message=f"{sr.store_name} caiu {abs(variacao):.1f}% no faturamento.",
                        suggestion="Acompanhe por mais uma semana e acione se persistir.",
                    ))

    # 6. Pior loja (margem muito baixa)
    for sr in store_results:
        if sr.margem_pct < 0:
            alerts.append(Alert(
                level="danger",
                title=f"{sr.store_name} com Margem Negativa",
                message=f"{sr.store_name} operou com margem de {sr.margem_pct:.1f}%.",
                suggestion="Revise os custos específicos desta unidade. Verifique se há "
                           "desperdício, furto ou custos alocados incorretamente.",
            ))

    # 7. Custo operacional muito alto
    if result.custo_pct > IDEAL_CUSTO_PCT:
        alerts.append(Alert(
            level="warning",
            title="Custo Operacional Alto",
            message=f"Os custos representam {result.custo_pct:.1f}% do faturamento.",
            suggestion="Mapeie os 3 maiores custos e negocie redução. Foco em aluguel, folha "
                       "e matéria-prima — geralmente respondem por 70% do total.",
        ))

    # Positivo: tudo bem
    if not alerts:
        alerts.append(Alert(
            level="info",
            title="Operação Saudável",
            message=f"Margem de {result.margem_pct:.1f}% com resultado positivo de "
                    f"R$ {result.resultado:,.2f}.",
            suggestion="Continue monitorando semanalmente. Considere reinvestir parte do lucro "
                       "em marketing para aumentar faturamento.",
        ))

    return alerts
