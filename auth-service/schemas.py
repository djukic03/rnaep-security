from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    password: str
    role: str
    
class UserCreate(BaseModel):
    username: str
    password: str
    
class TokenRequest(BaseModel):
    auth_code: str