"""
Módulo 2 — Custos
Pergunta: Quanto gastou? Onde gastou?
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.cost import Cost


def total_costs(db: Session, month: int, year: int) -> float:
    result = db.query(func.sum(Cost.amount)).filter(
        extract("month", Cost.date) == month,
        extract("year", Cost.date) == year,
    ).scalar()
    return round(result or 0.0, 2)


def costs_by_category(db: Session, month: int, year: int) -> dict[str, float]:
    rows = (
        db.query(Cost.category, func.sum(Cost.amount))
        .filter(extract("month", Cost.date) == month, extract("year", Cost.date) == year)
        .group_by(Cost.category)
        .all()
    )
    return {row[0] or "Outros": round(row[1], 2) for row in rows}


def costs_by_subcategory(db: Session, month: int, year: int) -> list[dict]:
    rows = (
        db.query(Cost.category, Cost.subcategory, func.sum(Cost.amount))
        .filter(extract("month", Cost.date) == month, extract("year", Cost.date) == year)
        .group_by(Cost.category, Cost.subcategory)
        .order_by(Cost.category, func.sum(Cost.amount).desc())
        .all()
    )
    return [
        {"categoria": r[0], "subcategoria": r[1], "valor": round(r[2], 2)}
        for r in rows
    ]


def costs_by_unit(db: Session, month: int, year: int) -> dict[str, float]:
    rows = (
        db.query(Cost.unit, func.sum(Cost.amount))
        .filter(extract("month", Cost.date) == month, extract("year", Cost.date) == year)
        .group_by(Cost.unit)
        .all()
    )
    return {row[0]: round(row[1], 2) for row in rows}


def costs_growth(db: Session, month: int, year: int) -> float:
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    current = total_costs(db, month, year)
    previous = total_costs(db, prev_month, prev_year)
    if previous == 0:
        return 0.0
    return round((current - previous) / previous * 100, 2)
