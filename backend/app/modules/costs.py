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


def top_costs(db: Session, month: int, year: int, limit: int = 10) -> list[dict]:
    """Retorna os maiores custos individuais do mês."""
    rows = (
        db.query(Cost)
        .filter(
            extract("month", Cost.date) == month,
            extract("year", Cost.date) == year,
        )
        .order_by(Cost.amount.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "date": str(r.date),
            "description": r.description,
            "amount": r.amount,
            "category": r.category or "Outros",
            "subcategory": r.subcategory or "—",
            "unit": r.unit,
        }
        for r in rows
    ]


def growing_costs(
    current_cat: dict[str, float],
    prev_cat: dict[str, float],
) -> list[dict]:
    """Retorna categorias que cresceram mais vs mês anterior, com impacto em R$."""
    results = []
    for cat, val_atual in current_cat.items():
        val_prev = prev_cat.get(cat, 0.0)
        delta = val_atual - val_prev
        pct = round((delta / val_prev) * 100, 1) if val_prev > 0 else 0.0
        results.append({
            "categoria": cat,
            "atual": round(val_atual, 2),
            "anterior": round(val_prev, 2),
            "delta": round(delta, 2),
            "delta_pct": pct,
        })
    results.sort(key=lambda x: x["delta"], reverse=True)
    return [r for r in results if r["delta"] > 0]


def pareto_costs(db: Session, month: int, year: int) -> list[dict]:
    """Retorna subcategorias ordenadas por valor com % acumulada (curva de Pareto)."""
    rows = costs_by_subcategory(db, month, year)
    total = sum(r["valor"] for r in rows)
    if total == 0:
        return []
    rows_sorted = sorted(rows, key=lambda x: x["valor"], reverse=True)
    acumulado = 0.0
    result = []
    for r in rows_sorted:
        acumulado += r["valor"]
        result.append({
            "label": f"{r['categoria']} / {r['subcategoria']}",
            "valor": r["valor"],
            "pct": round(r["valor"] / total * 100, 1),
            "pct_acumulada": round(acumulado / total * 100, 1),
        })
    return result
