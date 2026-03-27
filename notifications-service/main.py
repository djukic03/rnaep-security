from fastapi import FastAPI, Request
from typing import List
from schemas import Notification
from shared.logger import get_logger, setup_metrics
import time

app = FastAPI(title="Notifications Service")
logger = get_logger("notifications-service")
setup_metrics(app, "notifications-service")

notifications_db: List[Notification] = []

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
        "service": "notifications-service",
    })
    return response

@app.get("/notifications", response_model=List[Notification])
def get_notifications():
    return notifications_db

@app.post("/notifications", response_model=Notification)
def create_notification(notification: Notification):
    notifications_db.append(notification)

    logger.info("notification_sent", extra={
        "order_id": notification.order_id,
        "product_id": notification.product_id,
        "user_id": notification.user_id,
        "service": "notifications-service",
    })

    return notification