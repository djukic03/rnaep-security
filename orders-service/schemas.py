from pydantic import BaseModel
from typing import Optional

class Order(BaseModel): 
    id: int 
    product_id: int 
    quantity: int 
    note: Optional[str] = None