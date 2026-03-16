from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, engine
from typing import List
import requests
import models, schemas

app = FastAPI(title="Orders Service")

PRODUCTS_URL = "http://products-service:8000/products"
NOTIFICATIONS_URL = "http://notifications-service:8000/notifications"

models.Base.metadata.create_all(bind=engine)

@app.get("/orders", response_model=List[schemas.Order])
def get_orders(db: Session = Depends(get_db)):
    return db.query(models.OrderModel).all()

@app.post("/orders", response_model=schemas.Order)
def create_order(order: schemas.Order, db: Session = Depends(get_db)):
    response = requests.get(f"{PRODUCTS_URL}/{order.product_id}")
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Product not found")

    product = response.json()
    if product["quantity"] < order.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")
    
    requests.put(f"{PRODUCTS_URL}/{order.product_id}/reduce", params={"quantity": order.quantity})

    new_order = models.OrderModel(
        product_id=order.product_id, 
        quantity=order.quantity, 
        note=order.note
    )
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    requests.post(NOTIFICATIONS_URL, json={
        "order_id": order.id,
        "product_id": order.product_id,
        "message": f"Order {order.id} for product {order.product_id} has been placed."
    })

    return new_order