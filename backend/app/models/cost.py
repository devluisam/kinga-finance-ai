from sqlalchemy import Column, Integer, String, Float, Date, DateTime, func
from app.database import Base


class Cost(Base):
    __tablename__ = "costs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    description = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(100), nullable=True)     # classificação automática
    subcategory = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=False)         # fabrica, loja_01, loja_02, admin
    source = Column(String(50), default="manual")
    created_at = Column(DateTime, server_default=func.now())
