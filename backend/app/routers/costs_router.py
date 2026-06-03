from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
import csv, io

from app.database import get_db
from app.models.cost import Cost
from app.modules.classifier import classify, unit_from_description, RULES

router = APIRouter(prefix="/costs", tags=["Custos"])

CATEGORIES = sorted({r[0] for r in RULES})
SUBCATEGORIES: dict[str, list[str]] = {}
for _, cat, subcat, _ in [(None, r[0], r[1], r[2]) for r in RULES]:
    SUBCATEGORIES.setdefault(cat, [])
    if subcat not in SUBCATEGORIES[cat]:
        SUBCATEGORIES[cat].append(subcat)

UNITS = ["fabrica", "loja_01", "loja_02", "loja_03", "admin"]


class CostIn(BaseModel):
    date: date
    description: str
    amount: float
    unit: Optional[str] = None
    category: Optional[str] = Field(None)
    subcategory: Optional[str] = None


@router.get("/categories")
def get_categories():
    return {"categories": CATEGORIES, "subcategories": SUBCATEGORIES, "units": UNITS}


@router.get("/")
def list_costs(
    month: int = Query(...),
    year: int  = Query(...),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Cost)
        .filter(extract("month", Cost.date) == month, extract("year", Cost.date) == year)
        .order_by(Cost.date.desc(), Cost.amount.desc())
        .all()
    )
    return [
        {
            "id": c.id, "date": str(c.date), "description": c.description,
            "amount": c.amount, "category": c.category,
            "subcategory": c.subcategory, "unit": c.unit, "source": c.source,
        }
        for c in rows
    ]


@router.post("/", status_code=201)
def create_cost(payload: CostIn, db: Session = Depends(get_db)):
    override = f"{payload.category}/{payload.subcategory}" if payload.category else None
    cls = classify(payload.description, override)
    unit = payload.unit or unit_from_description(payload.description)
    cost = Cost(
        date=payload.date,
        description=payload.description,
        amount=payload.amount,
        category=cls.category,
        subcategory=cls.subcategory,
        unit=unit,
        source="manual",
    )
    db.add(cost)
    db.commit()
    db.refresh(cost)
    return {
        "id": cost.id,
        "category": cls.category,
        "subcategory": cls.subcategory,
        "unit": unit,
    }


@router.put("/{cost_id}")
def update_cost(cost_id: int, payload: CostIn, db: Session = Depends(get_db)):
    cost = db.get(Cost, cost_id)
    if not cost:
        raise HTTPException(404, "Custo não encontrado")
    override = f"{payload.category}/{payload.subcategory}" if payload.category else None
    cls = classify(payload.description, override)
    cost.date        = payload.date
    cost.description = payload.description
    cost.amount      = payload.amount
    cost.unit        = payload.unit or unit_from_description(payload.description)
    cost.category    = cls.category
    cost.subcategory = cls.subcategory
    db.commit()
    return {"message": "Custo atualizado."}


@router.delete("/{cost_id}", status_code=204)
def delete_cost(cost_id: int, db: Session = Depends(get_db)):
    cost = db.get(Cost, cost_id)
    if not cost:
        raise HTTPException(404, "Custo não encontrado")
    db.delete(cost)
    db.commit()


@router.patch("/{cost_id}/classify")
def reclassify(
    cost_id: int,
    category: str,
    subcategory: str,
    unit: Optional[str] = None,
    db: Session = Depends(get_db),
):
    cost = db.get(Cost, cost_id)
    if not cost:
        raise HTTPException(404, "Custo não encontrado")
    cost.category    = category
    cost.subcategory = subcategory
    if unit:
        cost.unit = unit
    db.commit()
    return {"message": "Classificação atualizada."}


@router.post("/upload-csv")
async def upload_costs_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """CSV esperado: date,description,amount,unit"""
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    count = 0
    for row in reader:
        try:
            desc = row["description"]
            cls  = classify(desc)
            unit = row.get("unit") or unit_from_description(desc)
            db.add(Cost(
                date=date.fromisoformat(row["date"]),
                description=desc,
                amount=float(row["amount"]),
                category=cls.category,
                subcategory=cls.subcategory,
                unit=unit,
                source="csv",
            ))
            count += 1
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Erro na linha {count + 1}: {e}")
    db.commit()
    return {"importados": count}
