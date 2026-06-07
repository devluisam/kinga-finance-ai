from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules import billing, costs as costs_mod
from app.modules.agent import run_report

router = APIRouter(prefix="/report", tags=["Relatório"])

_MONTHS_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


@router.get("/annual/{year}")
def get_annual(year: int, db: Session = Depends(get_db)):
    """Retorna faturamento, custos e resultado para todos os 12 meses do ano."""
    months = []
    for m in range(1, 13):
        fat = billing.total_revenue(db, m, year)
        custo = costs_mod.total_costs(db, m, year)
        resultado = round(fat - custo, 2)
        margem = round(resultado / fat * 100, 2) if fat > 0 else 0.0
        months.append({
            "month": m,
            "month_name": _MONTHS_PT[m],
            "month_short": _MONTHS_PT[m][:3],
            "faturamento": fat,
            "custos": custo,
            "resultado": resultado,
            "margem_pct": margem,
        })
    total_fat = sum(m["faturamento"] for m in months)
    total_custo = sum(m["custos"] for m in months)
    return {
        "year": year,
        "months": months,
        "total_faturamento": round(total_fat, 2),
        "total_custos": round(total_custo, 2),
        "total_resultado": round(total_fat - total_custo, 2),
    }


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
        "forecast": asdict(report.forecast),
        "health": asdict(report.health),
        "channel_revenue": report.channel_revenue,
        "narrative": report.narrative,
    }
