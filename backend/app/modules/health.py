"""
Módulo de Score de Saúde Financeira.
Calcula um índice 0-100 e um grau qualitativo com base nos principais KPIs.
"""
from dataclasses import dataclass

from app.modules.results import OperationalResult


@dataclass
class HealthScore:
    score: float            # 0 a 100
    grade: str              # "Excelente" | "Bom" | "Atenção" | "Crítico"
    grade_color: str        # cor hex para o dashboard
    detalhes: dict[str, float]   # pontuação por dimensão


# Pesos de cada dimensão (somam 100)
_PESO_MARGEM = 35
_PESO_CRESCIMENTO = 25
_PESO_CONTROLE_CUSTO = 25
_PESO_RESULTADO = 15


def compute_health(
    result: OperationalResult,
    stores_count: int = 0,
    stores_negativas: int = 0,
) -> HealthScore:
    """
    Calcula o score de saúde financeira.

    Dimensões:
      1. Margem operacional (35 pts)
      2. Crescimento de faturamento (25 pts)
      3. Controle de custos (25 pts)
      4. Resultado positivo + estabilidade (15 pts)
    """
    detalhes: dict[str, float] = {}

    # 1. Margem operacional
    m = result.margem_pct
    if m >= 35:
        p_margem = _PESO_MARGEM
    elif m >= 25:
        p_margem = round(_PESO_MARGEM * 0.88)
    elif m >= 15:
        p_margem = round(_PESO_MARGEM * 0.72)
    elif m >= 8:
        p_margem = round(_PESO_MARGEM * 0.50)
    elif m >= 0:
        p_margem = round(_PESO_MARGEM * 0.22)
    else:
        p_margem = 0
    detalhes["margem"] = p_margem

    # 2. Crescimento de faturamento
    g = result.variacao_faturamento
    if g >= 15:
        p_cresc = _PESO_CRESCIMENTO
    elif g >= 8:
        p_cresc = round(_PESO_CRESCIMENTO * 0.84)
    elif g >= 3:
        p_cresc = round(_PESO_CRESCIMENTO * 0.68)
    elif g >= 0:
        p_cresc = round(_PESO_CRESCIMENTO * 0.52)
    elif g >= -5:
        p_cresc = round(_PESO_CRESCIMENTO * 0.28)
    else:
        p_cresc = 0
    detalhes["crescimento"] = p_cresc

    # 3. Controle de custos (custos crescendo menos que vendas = bom)
    diff = result.variacao_custos - result.variacao_faturamento
    if diff <= -5:
        p_custo = _PESO_CONTROLE_CUSTO          # custos caindo enquanto vendas crescem
    elif diff <= 0:
        p_custo = round(_PESO_CONTROLE_CUSTO * 0.84)
    elif diff <= 3:
        p_custo = round(_PESO_CONTROLE_CUSTO * 0.60)
    elif diff <= 8:
        p_custo = round(_PESO_CONTROLE_CUSTO * 0.32)
    else:
        p_custo = 0
    detalhes["controle_custo"] = p_custo

    # 4. Resultado e estabilidade das lojas
    p_res = 0
    if result.status == "LUCRO":
        p_res = _PESO_RESULTADO
    elif result.status == "EQUILÍBRIO":
        p_res = round(_PESO_RESULTADO * 0.40)
    # Desconto se muitas lojas com margem negativa
    if stores_count > 0:
        pct_neg = stores_negativas / stores_count
        p_res = round(p_res * (1 - pct_neg * 0.5))
    detalhes["resultado"] = p_res

    score = round(min(p_margem + p_cresc + p_custo + p_res, 100), 1)

    if score >= 80:
        grade = "Excelente"
        color = "#00C896"
    elif score >= 62:
        grade = "Bom"
        color = "#4CC9F0"
    elif score >= 42:
        grade = "Atenção"
        color = "#FFB347"
    else:
        grade = "Crítico"
        color = "#FF4B4B"

    return HealthScore(score=score, grade=grade, grade_color=color, detalhes=detalhes)
