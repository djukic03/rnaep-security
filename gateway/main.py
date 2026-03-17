from fastapi import FastAPI, Request, Header, Depends, HTTPException, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
import jwt

app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "RNAEP_ELAB"
ALGORITHM = "HS256"

AUTH_URL = "http://auth-service:8000"
PRODUCTS_URL = "http://products-service:8000/products"
ORDERS_URL = "http://orders-service:8000/orders"
NOTIFICATIONS_URL = "http://notifications-service:8000/notifications"

def verify_token(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Token nije prosleđen")
    
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token je istekao")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Neispravan token")

def verify_admin(payload: dict = Depends(verify_token)):
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Pristup odbijen!")

@app.get("/users")
def get_users(payload: dict = Depends(verify_admin)):
    response = requests.get(AUTH_URL + "/users")
    return JSONResponse(content=response.json())

@app.post("/register")
def register(user: dict):
    response = requests.post(AUTH_URL + "/register", json=user)
    return JSONResponse(content=response.json(), status_code=response.status_code)
    
@app.get("/authorize")
def authorize_form(client_id: str, redirect_uri: str):
    response = requests.get(f"{AUTH_URL}/authorize?client_id={client_id}&redirect_uri={redirect_uri}")
    return HTMLResponse(content=response.text)

@app.post("/authorize")
async def authorize(request: Request):
    form_data = await request.form()
    response = requests.post(
        f"{AUTH_URL}/authorize",
        data=dict(form_data),
        allow_redirects=False
    )
    if response.status_code == 302:
        return RedirectResponse(url=response.headers["location"], status_code=302)
    return HTMLResponse(content=response.text)

@app.post("/token")
def token(body: dict, response: Response):
    res = requests.post(AUTH_URL + "/token", json=body)
    if res.status_code != 200:
        return JSONResponse(content=res.json(), status_code=res.status_code)
    data = res.json()
    response.set_cookie(
        key="access_token",
        value=data["access_token"],
        httponly=True,
        samesite="strict"
    )
    return {"role": data["role"]}
    
@app.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Uspešna odjava"}




@app.get("/products")
def get_products():
    response = requests.get(PRODUCTS_URL)
    return JSONResponse(content=response.json())

@app.get("/orders")
def get_orders(payload: dict = Depends(verify_token)):
    user_id = payload.get("id")
    response = requests.get(f"{ORDERS_URL}?user_id={user_id}")
    return JSONResponse(content=response.json())

@app.post("/orders")
def create_order(order: dict, payload: dict = Depends(verify_token)):
    order["user_id"] = payload.get("id")
    response = requests.post(ORDERS_URL, json=order)
    return JSONResponse(content=response.json())

@app.get("/notifications")
def get_notifications():
    response = requests.get(NOTIFICATIONS_URL)
    return JSONResponse(content=response.json())