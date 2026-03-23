from fastapi import FastAPI, HTTPException, Depends, Header, Request
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas, jwt
import os, time
from shared.logger import get_logger

app = FastAPI(title="Products Service")
logger = get_logger("products-service")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


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
        "service": "products-service",
    })
    return response

def verify_service_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("token_missing", extra={
            "service": "products-service",
        })
        raise HTTPException(status_code=401, detail="Token nije prosleđen")

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("sub") != "orders-service":
            logger.warning("unauthorized_caller", extra={
                "caller": payload.get("sub"),
                "service": "products-service",
            })
            raise HTTPException(status_code=403, detail="Neovlašćen pristup")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("token_expired", extra={
            "service": "products-service",
        })
        raise HTTPException(status_code=401, detail="Token je istekao")
    except jwt.InvalidTokenError:
        logger.warning("token_invalid", extra={
            "service": "products-service",
        })
        raise HTTPException(status_code=401, detail="Neispravan token")

@app.get("/products", response_model=List[schemas.Product])
def get_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()

    logger.info("products_fetched", extra={
        "count": len(products),
        "service": "products-service",
    })
    return products

@app.get("/products/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db), payload: dict = Depends(verify_service_token)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        logger.warning("product_not_found", extra={
            "product_id": product_id,
            "service": "products-service",
        })
        raise HTTPException(status_code=404, detail="Product not found")

    logger.info("product_fetched", extra={
        "product_id": product_id,
        "service": "products-service",
    })
    return product

@app.put("/products/{product_id}/reduce", response_model=schemas.Product)
def reduce_quantity(product_id: int, quantity: int, db: Session = Depends(get_db), payload: dict = Depends(verify_service_token)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        logger.warning("product_not_found", extra={
            "product_id": product_id,
            "service": "products-service",
        })
        raise HTTPException(status_code=404, detail="Product not found")

    if product.quantity < quantity:
        logger.warning("insufficient_stock", extra={
            "product_id": product_id,
            "requested": quantity,
            "available": product.quantity,
            "service": "products-service",
        })
        raise HTTPException(status_code=400, detail="Not enough stock")

    product.quantity -= quantity
    db.commit()
    db.refresh(product)

    logger.info("stock_reduced", extra={
        "product_id": product_id,
        "reduced_by": quantity,
        "remaining": product.quantity,
        "service": "products-service",
    })
    return product