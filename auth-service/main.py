from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
import models

app = FastAPI(title="Auth Service")

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()