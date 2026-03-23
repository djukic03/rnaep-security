from fastapi import FastAPI, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from database import get_db, engine
from typing import List
import requests
import models, schemas
import os, time
from shared.logger import get_logger

app = FastAPI(title="Orders Service")
logger = get_logger("orders-service")

PRODUCTS_URL = "http://products-service:8000/products"
NOTIFICATIONS_URL = "http://notifications-service:8000/notifications"
AUTH_URL = "http://auth-service:8000"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

models.Base.metadata.create_all(bind=engine)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)

    logger.info("http_request", extra={
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
        "service": "orders-service",
    })
    return response


def get_service_token():
    response = requests.post(f"{AUTH_URL}/token/service", json={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    })
    if response.status_code == 200:
        return response.json().get("access_token")

    logger.error("service_token_failed", extra={
        "status_code": response.status_code,
        "service": "orders-service",
    })
    return None


@app.get("/orders", response_model=List[schemas.Order])
def get_orders(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(models.OrderModel).filter(models.OrderModel.user_id == user_id).all()

    logger.info("orders_fetched", extra={
        "user_id": user_id,
        "count": len(orders),
        "service": "orders-service",
    })
    return orders

@app.post("/orders", response_model=schemas.Order)
def create_order(order: schemas.Order, db: Session = Depends(get_db)):
    service_token = get_service_token()
    headers = {"Authorization": f"Bearer {service_token}"}

    response = requests.get(f"{PRODUCTS_URL}/{order.product_id}", headers=headers)
    if response.status_code != 200:
        logger.error("product_not_found", extra={
            "product_id": order.product_id,
            "service": "orders-service",
        })
        raise HTTPException(status_code=404, detail="Product not found")

    product = response.json()
    if product["quantity"] < order.quantity:
        logger.error("insufficient_stock", extra={
            "product_id": order.product_id,
            "requested": order.quantity,
            "available": product["quantity"],
            "service": "orders-service",
        })
        raise HTTPException(status_code=400, detail="Not enough stock")

    requests.put(f"{PRODUCTS_URL}/{order.product_id}/reduce", params={"quantity": order.quantity}, headers=headers)

    new_order = models.OrderModel(
        user_id=order.user_id,
        product_id=order.product_id,
        quantity=order.quantity,
        note=order.note
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    logger.info("order_created", extra={
        "order_id": new_order.id,
        "user_id": new_order.user_id,
        "product_id": new_order.product_id,
        "quantity": new_order.quantity,
        "service": "orders-service",
    })

    requests.post(NOTIFICATIONS_URL, json={
        "order_id": new_order.id,
        "user_id": new_order.user_id,
        "product_id": new_order.product_id,
        "message": f"Order {new_order.id} for product {new_order.product_id} has been placed by user {new_order.user_id}."
    })

    return new_order