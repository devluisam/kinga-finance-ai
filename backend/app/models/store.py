from sqlalchemy import Column, String, Boolean, DateTime, func
from app.database import Base


class Store(Base):
    __tablename__ = "stores"

    store_id   = Column(String(50), primary_key=True)
    store_name = Column(String(100), nullable=False)
    active     = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
