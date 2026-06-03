from sqlalchemy import Column, Integer, String, Float, Date, DateTime, func
from app.database import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    store_id = Column(String(50), nullable=False, index=True)
    store_name = Column(String(100), nullable=False)
    channel = Column(String(50), default="pdv")  # pdv, ifood, delivery
    amount = Column(Float, nullable=False)
    source = Column(String(50), default="manual")  # manual, api, csv
    created_at = Column(DateTime, server_default=func.now())
