"""
Módulo de Projeção de Fechamento do Mês.
Com base no ritmo diário acumulado, projeta receitas, custos e resultado final.
"""
import calendar
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.cost import Cost
from app.models.sale import Sale


@dataclass
class ForecastReport:
    dia_atual: int
    total_dias: int
    dias_restantes: int
    pct_mes_decorrido: float
    # Acumulado até hoje
    fat_atual: float
    custo_atual: float
    resultado_atual: float
    # Ritmo diário médio
    fat_diario: float
    custo_diario: float
    # Projeção para o fechamento
    fat_projetado: float
    custo_projetado: float
    resultado_projetado: float
    margem_projetada: float
    # Break-even
    break_even_dias: float          # dias de vendas (no ritmo atual) para cobrir os custos projetados
    break_even_pct_mes: float       # break_even_dias / total_dias × 100
    # Comparação com referência (mês anterior)
    fat_referencia: float
    variacao_vs_referencia: float
    tendencia: str                  # "ACIMA" | "ABAIXO" | "NO_RITMO" | "SEM_REFERENCIA"
    fat_diario_necessario: float


def project_month(
    db: Session,
    month: int,
    year: int,
    fat_mes_anterior: float = 0.0,
) -> ForecastReport:
    today = date.today()
    total_dias = calendar.monthrange(year, month)[1]

    # Para mês corrente usa o dia de hoje; para meses fechados usa o total
    if year == today.year and month == today.month:
        dia_atual = today.day
    else:
        dia_atual = total_dias

    dias_restantes = total_dias - dia_atual
    pct_decorrido = round(dia_atual / total_dias * 100, 1)

    # Acumulado
    fat_atual = float(
        db.query(func.sum(Sale.amount)).filter(
            extract("month", Sale.date) == month,
            extract("year", Sale.date) == year,
        ).scalar() or 0.0
    )
    custo_atual = float(
        db.query(func.sum(Cost.amount)).filter(
            extract("month", Cost.date) == month,
            extract("year", Cost.date) == year,
        ).scalar() or 0.0
    )
    resultado_atual = round(fat_atual - custo_atual, 2)

    # Ritmo diário médio
    fat_diario = round(fat_atual / dia_atual, 2) if dia_atual > 0 else 0.0
    custo_diario = round(custo_atual / dia_atual, 2) if dia_atual > 0 else 0.0

    # Projeção linear para o total do mês
    fat_projetado = round(fat_diario * total_dias, 2)
    custo_projetado = round(custo_diario * total_dias, 2)
    resultado_projetado = round(fat_projetado - custo_projetado, 2)
    margem_projetada = round(
        resultado_projetado / fat_projetado * 100, 2
    ) if fat_projetado > 0 else 0.0

    # Comparação com mês anterior
    if fat_mes_anterior > 0 and fat_projetado > 0:
        variacao = round((fat_projetado - fat_mes_anterior) / fat_mes_anterior * 100, 1)
        if variacao > 3:
            tendencia = "ACIMA"
        elif variacao < -3:
            tendencia = "ABAIXO"
        else:
            tendencia = "NO_RITMO"
    else:
        variacao = 0.0
        tendencia = "SEM_REFERENCIA"

    # Ritmo necessário para igualar o mês anterior nos dias restantes
    if fat_mes_anterior > 0 and dias_restantes > 0:
        fat_necessario_restante = fat_mes_anterior - fat_atual
        fat_diario_necessario = round(
            max(fat_necessario_restante, 0) / dias_restantes, 2
        )
    else:
        fat_diario_necessario = fat_diario

    # Break-even: quantos dias de vendas (no ritmo atual) cobrem os custos projetados
    break_even_dias = round(custo_projetado / fat_diario, 1) if fat_diario > 0 else 0.0
    break_even_pct = round(break_even_dias / total_dias * 100, 1) if total_dias > 0 else 0.0

    return ForecastReport(
        dia_atual=dia_atual,
        total_dias=total_dias,
        dias_restantes=dias_restantes,
        pct_mes_decorrido=pct_decorrido,
        fat_atual=round(fat_atual, 2),
        custo_atual=round(custo_atual, 2),
        resultado_atual=resultado_atual,
        fat_diario=fat_diario,
        custo_diario=custo_diario,
        fat_projetado=fat_projetado,
        custo_projetado=custo_projetado,
        resultado_projetado=resultado_projetado,
        margem_projetada=margem_projetada,
        break_even_dias=break_even_dias,
        break_even_pct_mes=break_even_pct,
        fat_referencia=round(fat_mes_anterior, 2),
        variacao_vs_referencia=variacao,
        tendencia=tendencia,
        fat_diario_necessario=fat_diario_necessario,
    )
