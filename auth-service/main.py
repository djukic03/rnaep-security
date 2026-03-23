from fastapi import FastAPI, HTTPException, Depends, Request, Form
from sqlalchemy.orm import Session
from database import get_db
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import models, schemas, uuid, jwt
from datetime import datetime, timedelta
import os, json, time
from pwdlib import PasswordHash
from shared.logger import get_logger

password_hash = PasswordHash.recommended()

TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Auth Service")
templates = Jinja2Templates(directory="templates")
auth_codes = {}

logger = get_logger("auth-service")

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
        "service": "auth-service",
    })
    return response

#############################
#       ACG flow
############################

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    exist = db.query(models.User).filter(models.User.username == user.username).first()
    if exist:
        logger.error("register_failed_duplicate", extra={
            "username": user.username,
            "service": "auth-service",
        })
        raise HTTPException(status_code=400, detail="Korisničko ime već postoji")

    new_user = models.User(
        username=user.username,
        password=password_hash.hash(user.password),
        role="user"
    )
    db.add(new_user)
    db.commit()

    logger.info("user_registered", extra={
        "username": user.username,
        "service": "auth-service",
    })
    return {"message": "Korisnik uspešno registrovan"}


@app.get("/authorize", response_class=HTMLResponse)
def authorize_form(request: Request, client_id: str, redirect_uri: str):
    logger.info("authorize_form_opened", extra={
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "service": "auth-service",
    })
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "error": None
        }
    )
    
@app.post("/authorize")
def authorize(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    response_type: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user or not password_hash.verify(password, user.password):
        logger.error("login_failed", extra={
            "username": username,
            "client_id": client_id,
            "service": "auth-service",
        })
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "error": "Neispravni kredencijali"
            }
        )

    code = str(uuid.uuid4())
    auth_codes[code] = {"username": username, "role": user.role}

    logger.info("authorize_success", extra={
        "username": username,
        "client_id": client_id,
        "service": "auth-service",
    })
    return RedirectResponse(url=f"{redirect_uri}?code={code}", status_code=302)

@app.post("/token")
def token(code: schemas.TokenRequest, db: Session = Depends(get_db)):
    data = auth_codes.pop(code.auth_code, None)

    if not data:
        logger.error("token_invalid_code", extra={
            "auth_code": code.auth_code,
            "service": "auth-service",
        })
        raise HTTPException(status_code=400, detail="Nevažeći authorization code")

    user = db.query(models.User).filter(models.User.username == data['username']).first()

    payload = {
        "sub": user.username,
        "id": user.id,
        "role": user.role,
        "iss": "auth-service",
        "iat": datetime.now(),
        "exp": datetime.now() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    logger.info("token_issued", extra={
        "username": user.username,
        "role": user.role,
        "service": "auth-service",
    })
    return {
        "access_token": token,
        "role": user.role
    }
    
###############################
#      CCG flow
###############################

SERVICE_CLIENTS = json.loads(os.getenv("SERVICE_CLIENTS"))

@app.post("/token/service")
def service_token(credentials: schemas.ServiceTokenRequest):
    client_secret = SERVICE_CLIENTS.get(credentials.client_id)

    if not client_secret or client_secret != credentials.client_secret:
        logger.error("service_token_failed", extra={
            "client_id": credentials.client_id,
            "service": "auth-service",
        })
        raise HTTPException(status_code=401, detail="Neispravni kredencijali")

    payload = {
        "sub": credentials.client_id,
        "iss": "auth-service",
        "iat": datetime.now(),
        "exp": datetime.now() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    logger.info("service_token_issued", extra={
        "client_id": credentials.client_id,
        "service": "auth-service",
    })
    
    return {
        "access_token": token
    }