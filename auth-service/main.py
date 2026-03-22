from fastapi import FastAPI, HTTPException, Depends, Request, Form
from sqlalchemy.orm import Session
from database import get_db
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import models, schemas, uuid, jwt
from datetime import datetime, timedelta
import os, json
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Auth Service")
templates = Jinja2Templates(directory="templates")
auth_codes = {}


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
        raise HTTPException(status_code=400, detail="Korisničko ime već postoji")
    
    new_user = models.User(
        username=user.username,
        password=password_hash.hash(user.password),
        role="user"
    )
    db.add(new_user)
    db.commit()
    return {"message": "Korisnik uspešno registrovan"}


@app.get("/authorize", response_class=HTMLResponse)
def authorize_form(request: Request, client_id: str, redirect_uri: str):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "error": None
    })
    
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
        return templates.TemplateResponse("login.html", {
            "request": request,
            "response_type": response_type,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "error": "Pogrešno korisničko ime ili lozinka"
        })
    
    code = str(uuid.uuid4())
    auth_codes[code] = {"username": username, "role": user.role}
    
    return RedirectResponse(url=f"{redirect_uri}?code={code}", status_code=302)

@app.post("/token")
def token(code: schemas.TokenRequest, db: Session = Depends(get_db)):
    code = auth_codes.pop(code.auth_code, None)
    
    if not code:
        raise HTTPException(status_code=400, detail="Nevažeći authorization code")
    
    user = db.query(models.User).filter(models.User.username == code['username']).first()
    
    payload = {
        "sub": user.username,
        "id": user.id,
        "role": user.role,
        "iss": "auth-service",
        "iat": datetime.now(),
        "exp": datetime.now() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
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
        raise HTTPException(status_code=401, detail="Neispravni kredencijali")
    
    payload = {
        "sub": credentials.client_id,
        "iss": "auth-service",
        "iat": datetime.now(),
        "exp": datetime.now() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": token
    }