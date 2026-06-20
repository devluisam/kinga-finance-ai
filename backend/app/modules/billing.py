"""
Módulo 1 — Faturamento
Pergunta: Quanto vendeu?
"""
import calendar
from datetime import date as dt
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.sale import Sale


def total_revenue(db: Session, month: int, year: int) -> float:
    result = db.query(func.sum(Sale.amount)).filter(
        extract("month", Sale.date) == month,
        extract("year", Sale.date) == year,
    ).scalar()
    return round(result or 0.0, 2)


def revenue_by_store(db: Session, month: int, year: int) -> dict[str, float]:
    rows = (
        db.query(Sale.store_id, Sale.store_name, func.sum(Sale.amount))
        .filter(
            extract("month", Sale.date) == month,
            extract("year", Sale.date) == year,
        )
        .group_by(Sale.store_id, Sale.store_name)
        .all()
    )
    return {row[1]: round(row[2], 2) for row in rows}


def revenue_by_channel(db: Session, month: int, year: int) -> dict[str, float]:
    rows = (
        db.query(Sale.channel, func.sum(Sale.amount))
        .filter(extract("month", Sale.date) == month, extract("year", Sale.date) == year)
        .group_by(Sale.channel)
        .all()
    )
    return {row[0]: round(row[1], 2) for row in rows}


def revenue_growth(db: Session, month: int, year: int) -> float:
    """Crescimento percentual vs mês anterior."""
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    current = total_revenue(db, month, year)
    previous = total_revenue(db, prev_month, prev_year)
    if previous == 0:
        return 0.0
    return round((current - previous) / previous * 100, 2)


def daily_revenue_list(db: Session, month: int, year: int) -> list[dict]:
    """Receita dia a dia para o mês, preenchendo zeros onde não há vendas."""
    rows = (
        db.query(Sale.date, func.sum(Sale.amount))
        .filter(
            extract("month", Sale.date) == month,
            extract("year", Sale.date) == year,
        )
        .group_by(Sale.date)
        .order_by(Sale.date)
        .all()
    )
    n_days = calendar.monthrange(year, month)[1]
    daily: dict[dt, float] = {dt(year, month, d): 0.0 for d in range(1, n_days + 1)}
    for date_val, amount in rows:
        key = dt(date_val.year, date_val.month, date_val.day)
        if key in daily:
            daily[key] = round(float(amount), 2)
    return [{"date": str(d), "day": d.day, "amount": v} for d, v in sorted(daily.items())]


def weekly_revenue(db: Session, month: int, year: int) -> list[dict]:
    """Receita agrupada por semana do mês (semana 1–5)."""
    rows = (
        db.query(Sale.date, func.sum(Sale.amount))
        .filter(
            extract("month", Sale.date) == month,
            extract("year", Sale.date) == year,
        )
        .group_by(Sale.date)
        .order_by(Sale.date)
        .all()
    )
    buckets: dict[int, float] = {}
    for date_val, amount in rows:
        day = date_val.day if hasattr(date_val, "day") else dt.fromisoformat(str(date_val)).day
        week = (day - 1) // 7 + 1
        buckets[week] = round(buckets.get(week, 0.0) + float(amount), 2)
    return [{"semana": w, "faturamento": v} for w, v in sorted(buckets.items())]
