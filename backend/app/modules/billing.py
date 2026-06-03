"""
Módulo 1 — Faturamento
Pergunta: Quanto vendeu?
"""
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
import pandas as pd

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
        .filter(extract("month", Sale.date) == month, extract("year", Sale.date) == year)
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


def weekly_revenue(db: Session, month: int, year: int) -> list[dict]:
    rows = db.query(Sale.date, func.sum(Sale.amount)).filter(
        extract("month", Sale.date) == month,
        extract("year", Sale.date) == year,
    ).group_by(Sale.date).order_by(Sale.date).all()

    df = pd.DataFrame(rows, columns=["date", "amount"])
    if df.empty:
        return []
    df["week"] = pd.to_datetime(df["date"]).dt.isocalendar().week
    weekly = df.groupby("week")["amount"].sum().reset_index()
    return weekly.rename(columns={"week": "semana", "amount": "faturamento"}).to_dict("records")
