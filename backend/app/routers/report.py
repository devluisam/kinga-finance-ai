from dataclasses import asdict

from fastapi import APIRouter, Depends, Query
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
    """Faturamento, custos, resultado e breakdown de custos para os 12 meses do ano."""
    months = []
    for m in range(1, 13):
        fat = billing.total_revenue(db, m, year)
        custo = costs_mod.total_costs(db, m, year)
        resultado = round(fat - custo, 2)
        margem = round(resultado / fat * 100, 2) if fat > 0 else 0.0
        cat = costs_mod.costs_by_category(db, m, year) if (fat > 0 or custo > 0) else {}
        months.append({
            "month": m,
            "month_name": _MONTHS_PT[m],
            "month_short": _MONTHS_PT[m][:3],
            "faturamento": fat,
            "custos": custo,
            "resultado": resultado,
            "margem_pct": margem,
            "costs_by_category": cat,
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


@router.get("/compare")
def compare_months(
    m1: int = Query(..., description="Mês 1 (1-12)"),
    y1: int = Query(..., description="Ano 1"),
    m2: int = Query(..., description="Mês 2 (1-12)"),
    y2: int = Query(..., description="Ano 2"),
    db: Session = Depends(get_db),
):
    """Comparação lado a lado de dois meses."""
    fat1 = billing.total_revenue(db, m1, y1)
    fat2 = billing.total_revenue(db, m2, y2)
    custo1 = costs_mod.total_costs(db, m1, y1)
    custo2 = costs_mod.total_costs(db, m2, y2)
    res1 = round(fat1 - custo1, 2)
    res2 = round(fat2 - custo2, 2)
    cat1 = costs_mod.costs_by_category(db, m1, y1)
    cat2 = costs_mod.costs_by_category(db, m2, y2)
    stores1 = billing.revenue_by_store(db, m1, y1)
    stores2 = billing.revenue_by_store(db, m2, y2)
    ch1 = billing.revenue_by_channel(db, m1, y1)
    ch2 = billing.revenue_by_channel(db, m2, y2)

    def _pct(a: float, b: float) -> float:
        return round((a - b) / b * 100, 1) if b != 0 else 0.0

    def _marg(fat: float, custo: float) -> float:
        return round((fat - custo) / fat * 100, 1) if fat > 0 else 0.0

    return {
        "periodo_1": f"{_MONTHS_PT[m1]}/{y1}",
        "periodo_2": f"{_MONTHS_PT[m2]}/{y2}",
        "faturamento":  {"p1": fat1,   "p2": fat2,   "delta_pct": _pct(fat1, fat2)},
        "custos":       {"p1": custo1, "p2": custo2, "delta_pct": _pct(custo1, custo2)},
        "resultado":    {"p1": res1,   "p2": res2,   "delta_pct": _pct(res1, res2)},
        "margem":       {"p1": _marg(fat1, custo1), "p2": _marg(fat2, custo2)},
        "costs_by_category": {"p1": cat1, "p2": cat2},
        "revenue_by_store":  {"p1": stores1, "p2": stores2},
        "revenue_by_channel": {"p1": ch1, "p2": ch2},
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
        "daily_revenue": report.daily_revenue,
        "alerts": [asdict(a) for a in report.alerts],
        "forecast": asdict(report.forecast),
        "health": asdict(report.health),
        "channel_revenue": report.channel_revenue,
        "top_costs": report.top_costs,
        "growing_costs": report.growing_costs,
        "pareto_costs": report.pareto_costs,
        "narrative": report.narrative,
    }
