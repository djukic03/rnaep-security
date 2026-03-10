from sqlalchemy import Column, Integer, String
from database import Base

class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer)
    quantity = Column(Integer)
    note = Column(String, nullable=True)