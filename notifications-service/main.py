from fastapi import FastAPI
from typing import List
from models import Notification

app = FastAPI(title="Notifications Service")

notifications_db: List[Notification] = []

@app.get("/notifications", response_model=List[Notification])
def get_notifications():
    return notifications_db

@app.post("/notifications", response_model=Notification)
def create_notification(notification: Notification):
    notifications_db.append(notification)
    print(f"Notification sent: Order {notification.order_id} for product {notification.product_id} has been placed.")
    return notification