"""
Kinga Finance AI - Inicializador
Uso:
    python run.py           -> sobe a API (http://localhost:8000)
    python run.py dashboard -> sobe o dashboard Streamlit (http://localhost:8501)
    python run.py seed      -> apenas insere dados ficticios no banco
    python run.py report    -> imprime relatorio no terminal
"""
import sys
import os

# Fix encoding para Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Garante que o diretorio backend esta no path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))


def run_api():
    import uvicorn
    print("Iniciando Kinga Finance AI API...")
    print("  Docs:     http://localhost:8000/docs")
    print("  Relatorio: http://localhost:8000/report/2026/5")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


def run_dashboard():
    import subprocess
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
    print("Iniciando Dashboard Kinga Finance AI...")
    print("  URL: http://localhost:8501")
    python_exe = sys.executable
    subprocess.run([python_exe, "-m", "streamlit", "run", dashboard_path, "--server.port=8501"])


def run_seed():
    from app.database import SessionLocal, engine, Base
    from app.models import Sale, Cost  # noqa
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    from app.seed_data import seed
    seed(db)
    db.close()


def run_report_terminal():
    from app.database import SessionLocal, engine, Base
    from app.models import Sale, Cost  # noqa
    from app.modules.agent import run_report

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    from sqlalchemy import text
    count = db.execute(text("SELECT COUNT(*) FROM sales")).scalar()
    if count == 0:
        from app.seed_data import seed
        seed(db, clear=False)

    report = run_report(db, month=5, year=2026)
    db.close()

    sep = "=" * 62
    print(f"\n{sep}")
    print("  KINGA FINANCE AI -- RELATORIO 05/2026")
    print(sep)

    # Narrativa sem emojis para terminal Windows
    narrative_clean = (
        report.narrative
        .replace("✅", "[OK]").replace("❌", "[X]").replace("⚠️", "[!]")
        .replace("📊", "").replace("🏭", "").replace("🚨", "[URGENTE]")
        .replace("•", "-").replace("**", "")
    )
    print(narrative_clean)

    r = report.result
    print(f"\nRESULTADO OPERACIONAL")
    print(f"  Faturamento : R$ {r.faturamento:>12,.2f}   ({r.variacao_faturamento:+.1f}% vs mes anterior)")
    print(f"  Custos      : R$ {r.custos:>12,.2f}   ({r.variacao_custos:+.1f}% vs mes anterior)")
    print(f"  Resultado   : R$ {r.resultado:>12,.2f}")
    print(f"  Margem      : {r.margem_pct:.1f}%")
    print(f"  Status      : {r.status}")

    print(f"\nPOR LOJA")
    for s in report.store_results:
        print(f"  {s.store_name:<20}  Fat: R$ {s.faturamento:>10,.2f}  "
              f"Custo: R$ {s.custos:>9,.2f}  Margem: {s.margem_pct:>6.1f}%")

    f = report.factory
    print(f"\nFABRICA")
    print(f"  Custo total  : R$ {f.custos_totais:,.2f}")
    print(f"  Mat. prima   : R$ {f.materia_prima:,.2f}")
    print(f"  Folha        : R$ {f.folha:,.2f}  ({f.peso_folha:.1f}% dos custos fabrica)")
    print(f"  Energia      : R$ {f.energia:,.2f}")
    print(f"  % Faturamento: {f.pct_faturamento:.1f}%")

    level_label = {"danger": "[URGENTE]", "warning": "[ATENCAO]", "info": "[INFO]"}
    print(f"\nALERTAS INTELIGENTES")
    for a in report.alerts:
        lbl = level_label.get(a.level, "[INFO]")
        print(f"  {lbl} {a.title}")
        print(f"     {a.message}")
        print(f"     -> {a.suggestion}\n")

    print(sep)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "api"
    if cmd == "api":
        run_api()
    elif cmd == "dashboard":
        run_dashboard()
    elif cmd == "seed":
        run_seed()
    elif cmd == "report":
        run_report_terminal()
    else:
        print(f"Comando desconhecido: {cmd}")
        print("Use: api | dashboard | seed | report")
