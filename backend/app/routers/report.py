from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dataclasses import asdict

from app.database import get_db
from app.modules.agent import run_report

router = APIRouter(prefix="/report", tags=["Relatório"])


@router.get("/{year}/{month}")
def get_report(year: int, month: int, db: Session = Depends(get_db)):
    report = run_report(db, month, year)
    return {
        "period": f"{month:02d}/{year}",
        "result": asdict(report.result),
        "store_results": [asdict(s) for s in report.store_results],
        "factory": asdict(report.factory),
        "costs_by_category": report.costs_by_category,
        "costs_by_subcategory": report.costs_by_subcategory,
        "weekly_revenue": report.weekly_revenue,
        "alerts": [asdict(a) for a in report.alerts],
        "narrative": report.narrative,
    }
