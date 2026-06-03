"""
Módulo 7 — Fábrica
"""
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.cost import Cost


@dataclass
class FactoryReport:
    custos_totais: float
    materia_prima: float
    energia: float
    folha: float
    frete: float
    outros: float
    pct_faturamento: float
    peso_folha: float       # folha / custos_fabrica × 100


def factory_report(db: Session, month: int, year: int, faturamento_total: float) -> FactoryReport:
    rows = (
        db.query(Cost.subcategory, func.sum(Cost.amount))
        .filter(
            extract("month", Cost.date) == month,
            extract("year", Cost.date) == year,
            Cost.unit == "fabrica",
        )
        .group_by(Cost.subcategory)
        .all()
    )

    buckets: dict[str, float] = {r[0]: round(r[1], 2) for r in rows}
    total = sum(buckets.values())

    materia_prima = buckets.get("Matéria-prima", 0.0)
    energia = buckets.get("Energia", 0.0)
    folha = buckets.get("Funcionários", 0.0)
    frete = buckets.get("Frete", 0.0)
    outros = round(total - materia_prima - energia - folha - frete, 2)

    pct_fat = round(total / faturamento_total * 100, 2) if faturamento_total > 0 else 0.0
    peso_folha = round(folha / total * 100, 2) if total > 0 else 0.0

    return FactoryReport(
        custos_totais=total,
        materia_prima=materia_prima,
        energia=energia,
        folha=folha,
        frete=frete,
        outros=max(outros, 0.0),
        pct_faturamento=pct_fat,
        peso_folha=peso_folha,
    )
