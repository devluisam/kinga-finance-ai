from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.store import Store

router = APIRouter(prefix="/stores", tags=["Lojas"])


class StoreIn(BaseModel):
    store_id:   str
    store_name: str


@router.get("/")
def list_stores(db: Session = Depends(get_db)):
    rows = db.query(Store).order_by(Store.store_id).all()
    return [{"store_id": s.store_id, "store_name": s.store_name, "active": s.active} for s in rows]


@router.post("/", status_code=201)
def create_store(payload: StoreIn, db: Session = Depends(get_db)):
    if db.get(Store, payload.store_id):
        raise HTTPException(400, f"Loja '{payload.store_id}' já existe.")
    store = Store(store_id=payload.store_id, store_name=payload.store_name)
    db.add(store)
    db.commit()
    return {"message": f"Loja '{payload.store_name}' criada.", "store_id": payload.store_id}


@router.put("/{store_id}")
def update_store(store_id: str, payload: StoreIn, db: Session = Depends(get_db)):
    store = db.get(Store, store_id)
    if not store:
        raise HTTPException(404, "Loja não encontrada")
    store.store_name = payload.store_name
    db.commit()
    return {"message": "Loja atualizada."}


@router.patch("/{store_id}/toggle")
def toggle_store(store_id: str, db: Session = Depends(get_db)):
    store = db.get(Store, store_id)
    if not store:
        raise HTTPException(404, "Loja não encontrada")
    store.active = not store.active
    db.commit()
    return {"store_id": store_id, "active": store.active}
