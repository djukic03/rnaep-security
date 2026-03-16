from pydantic import BaseModel

class Notification(BaseModel):
    order_id: int
    user_id: int
    product_id: int
    message: str