import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

def _build_url() -> tuple[str, dict]:
    """Retorna (DATABASE_URL, connect_args) para SQLite local ou PostgreSQL na nuvem."""
    url = os.getenv("DATABASE_URL")

    if url:
        # Railway/Render fornecem postgres:// — SQLAlchemy precisa de postgresql+psycopg2://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        return url, {}

    # SQLite local — caminho absoluto fixo
    data_dir = os.getenv(
        "DATA_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")),
    )
    os.makedirs(data_dir, exist_ok=True)
    return f"sqlite:///{os.path.join(data_dir, 'kinga_finance.db')}", {"check_same_thread": False}


DATABASE_URL, _connect_args = _build_url()

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
