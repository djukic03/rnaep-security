from fastapi import FastAPI, Request, Header, Depends, HTTPException, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
import requests
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
import jwt, os, time
from shared.logger import get_logger

app = FastAPI(title="API Gateway")
logger = get_logger("api-gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

AUTH_URL = "http://auth-service:8000"
PRODUCTS_URL = "http://products-service:8000/products"
ORDERS_URL = "http://orders-service:8000/orders"
NOTIFICATIONS_URL = "http://notifications-service:8000/notifications"

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
        "service": "api-gateway",
    })
    return response

def verify_token(access_token: str = Cookie(None)):
    if not access_token:
        logger.warning("token_missing", extra={
            "service": "api-gateway",
        })
        raise HTTPException(status_code=401, detail="Token nije prosleđen")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("token_expired", extra={
            "service": "api-gateway",
        })
        raise HTTPException(status_code=401, detail="Token je istekao")
    except jwt.InvalidTokenError:
        logger.warning("token_invalid", extra={
            "service": "api-gateway",
        })
        raise HTTPException(status_code=401, detail="Neispravan token")

def verify_admin(payload: dict = Depends(verify_token)):
    if payload.get("role") != "admin":
        logger.warning("access_denied", extra={
            "user_id": payload.get("id"),
            "username": payload.get("sub"),
            "service": "api-gateway",
        })
        raise HTTPException(status_code=403, detail="Pristup odbijen!")
    return payload

@app.get("/users")
def get_users(payload: dict = Depends(verify_admin)):
    response = requests.get(AUTH_URL + "/users")
    return JSONResponse(content=response.json())

@app.post("/register")
def register(user: dict):
    response = requests.post(AUTH_URL + "/register", json=user)

    if response.status_code == 200:
        logger.info("user_registered", extra={
            "username": user.get("username"),
            "service": "api-gateway",
        })
    else:
        logger.warning("register_failed", extra={
            "username": user.get("username"),
            "status_code": response.status_code,
            "service": "api-gateway",
        })

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
        logger.info("authorize_redirect", extra={
            "username": form_data.get("username"),
            "client_id": form_data.get("client_id"),
            "service": "api-gateway",
        })
        return RedirectResponse(url=response.headers["location"], status_code=302)
    return HTMLResponse(content=response.text)

@app.post("/token")
def token(body: dict, response: Response):
    res = requests.post(AUTH_URL + "/token", json=body)
    if res.status_code != 200:
        logger.warning("token_exchange_failed", extra={
            "status_code": res.status_code,
            "service": "api-gateway",
        })
        return JSONResponse(content=res.json(), status_code=res.status_code)

    data = res.json()
    response.set_cookie(
        key="access_token",
        value=data["access_token"],
        httponly=True,
        samesite="strict"
    )

    logger.info("token_issued", extra={
        "role": data.get("role"),
        "service": "api-gateway",
    })
    
    return {"role": data["role"]}

@app.post("/logout")
def logout(response: Response, payload: dict = Depends(verify_token)):
    
    logger.info("user_logout", extra={
        "user_id": payload.get("id"),
        "username": payload.get("sub"),
        "service": "api-gateway",
    })
    
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

    logger.info("orders_fetched", extra={
        "user_id": user_id,
        "status_code": response.status_code,
        "service": "api-gateway",
    })
    
    return JSONResponse(content=response.json())

@app.post("/orders")
def create_order(order: dict, payload: dict = Depends(verify_token)):
    order["user_id"] = payload.get("id")
    response = requests.post(ORDERS_URL, json=order)

    logger.info("order_created", extra={
        "user_id": payload.get("id"),
        "status_code": response.status_code,
        "service": "api-gateway",
    })
    
    return JSONResponse(content=response.json())

@app.get("/notifications")
def get_notifications():
    response = requests.get(NOTIFICATIONS_URL)
    return JSONResponse(content=response.json())