from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas, jwt
import os

app = FastAPI(title="Products Service")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def verify_service_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token nije prosleđen")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("sub") != "orders-service":
            raise HTTPException(status_code=403, detail="Neovlašćen pristup")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token je istekao")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Neispravan token")

@app.get("/products", response_model=List[schemas.Product])
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@app.get("/products/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db), payload: dict = Depends(verify_service_token)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}/reduce", response_model=schemas.Product)
def reduce_quantity(product_id: int, quantity: int, db: Session = Depends(get_db), payload: dict = Depends(verify_service_token)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.quantity < quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")
    product.quantity -= quantity
    db.commit()
    db.refresh(product)
    return product