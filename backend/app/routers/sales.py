from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract
from pydantic import BaseModel
from datetime import date
import csv, io

from app.database import get_db
from app.models.sale import Sale

router = APIRouter(prefix="/sales", tags=["Vendas"])


class SaleIn(BaseModel):
    date: date
    store_id: str
    store_name: str
    channel: str = "pdv"
    amount: float


@router.get("/")
def list_sales(
    month: int = Query(...),
    year: int  = Query(...),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Sale)
        .filter(extract("month", Sale.date) == month, extract("year", Sale.date) == year)
        .order_by(Sale.date.desc())
        .all()
    )
    return [
        {
            "id": s.id, "date": str(s.date), "store_id": s.store_id,
            "store_name": s.store_name, "channel": s.channel,
            "amount": s.amount, "description": s.description or "",
            "source": s.source,
        }
        for s in rows
    ]


@router.post("/", status_code=201)
def create_sale(payload: SaleIn, db: Session = Depends(get_db)):
    sale = Sale(**payload.model_dump(), source="manual")
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return {"id": sale.id, "message": "Venda registrada."}


@router.put("/{sale_id}")
def update_sale(sale_id: int, payload: SaleIn, db: Session = Depends(get_db)):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(404, "Venda não encontrada")
    for k, v in payload.model_dump().items():
        setattr(sale, k, v)
    db.commit()
    return {"message": "Venda atualizada."}


@router.delete("/{sale_id}", status_code=204)
def delete_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(404, "Venda não encontrada")
    db.delete(sale)
    db.commit()


@router.post("/upload-csv")
async def upload_sales_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """CSV esperado: date,store_id,store_name,channel,amount"""
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    count = 0
    for row in reader:
        try:
            db.add(Sale(
                date=date.fromisoformat(row["date"]),
                store_id=row["store_id"],
                store_name=row["store_name"],
                channel=row.get("channel", "pdv"),
                amount=float(row["amount"]),
                source="csv",
            ))
            count += 1
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Erro na linha {count + 1}: {e}")
    db.commit()
    return {"importados": count}
