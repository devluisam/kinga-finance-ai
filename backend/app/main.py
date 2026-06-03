import os
import shutil
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import io

from app.database import engine, SessionLocal, DATABASE_URL
from app.models import Sale, Cost, Store  # noqa: F401
from app.database import Base
from app.routers import sales, costs_router, report, stores
from app.seed_data import seed

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Kinga Finance AI",
    description="Agente financeiro autônomo para Kinga Açaí Frozen",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sales.router)
app.include_router(costs_router.router)
app.include_router(report.router)
app.include_router(stores.router)


def _backup_db() -> str | None:
    """Cria backup do banco com timestamp. Retorna o caminho do backup."""
    if not DATABASE_URL.startswith("sqlite"):
        return None
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        return None
    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"kinga_finance_{ts}.db")
    shutil.copy2(db_path, backup_path)

    # Mantém apenas os 30 backups mais recentes
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".db")],
        reverse=True,
    )
    for old in backups[30:]:
        os.remove(os.path.join(backup_dir, old))

    return backup_path


@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        from sqlalchemy import text
        count = db.execute(text("SELECT COUNT(*) FROM sales")).scalar()
        if count == 0:
            print("[SEED] Nenhum dado encontrado. Inserindo dados de simulacao...")
            seed(db, clear=False)
        else:
            # Faz backup automático ao iniciar com dados reais
            backup = _backup_db()
            if backup:
                print(f"[BACKUP] Backup criado: {os.path.basename(backup)}")
    finally:
        db.close()


@app.get("/")
def root():
    return {"agent": "Kinga Finance AI", "version": "1.0.0",
            "docs": "/docs", "report_example": "/report/2026/5"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/backup")
def manual_backup():
    """Cria backup manual do banco de dados."""
    path = _backup_db()
    if not path:
        return {"message": "Backup não aplicável (banco não é SQLite local)."}
    return {"message": "Backup criado com sucesso.", "arquivo": os.path.basename(path)}


@app.get("/export/sales")
def export_sales():
    """Exporta todas as vendas como CSV."""
    from app.models.sale import Sale as SaleModel
    db = SessionLocal()
    try:
        rows = db.query(SaleModel).order_by(SaleModel.date).all()
        lines = ["date,store_id,store_name,channel,amount,source"]
        for r in rows:
            lines.append(f"{r.date},{r.store_id},{r.store_name},{r.channel},{r.amount},{r.source}")
        content = "\n".join(lines)
        return StreamingResponse(
            io.StringIO(content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=vendas_kinga.csv"},
        )
    finally:
        db.close()


@app.get("/export/costs")
def export_costs():
    """Exporta todos os custos como CSV."""
    from app.models.cost import Cost as CostModel
    db = SessionLocal()
    try:
        rows = db.query(CostModel).order_by(CostModel.date).all()
        lines = ["date,description,amount,category,subcategory,unit,source"]
        for r in rows:
            desc = r.description.replace(",", ";")
            lines.append(f"{r.date},{desc},{r.amount},{r.category},{r.subcategory},{r.unit},{r.source}")
        content = "\n".join(lines)
        return StreamingResponse(
            io.StringIO(content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=custos_kinga.csv"},
        )
    finally:
        db.close()


@app.get("/backup/list")
def list_backups():
    """Lista todos os backups disponíveis."""
    db_path = DATABASE_URL.replace("sqlite:///", "")
    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    if not os.path.exists(backup_dir):
        return {"backups": []}
    files = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".db")],
        reverse=True,
    )
    result = []
    for f in files:
        fp = os.path.join(backup_dir, f)
        result.append({
            "arquivo": f,
            "tamanho_kb": round(os.path.getsize(fp) / 1024, 1),
            "data": datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%d/%m/%Y %H:%M"),
        })
    return {"backups": result}
