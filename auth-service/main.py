from fastapi import FastAPI, HTTPException, Depends, Request, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import models, schemas, uuid, jwt
from datetime import datetime, timedelta

SECRET_KEY = "RNAEP_ELAB"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Auth Service")
templates = Jinja2Templates(directory="templates")
auth_codes = {}

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    exist = db.execute(text(f"SELECT * FROM users WHERE username = '{user.username}'")).fetchone()
    if exist:
        raise HTTPException(status_code=400, detail="Korisničko ime već postoji")
    
    new_user = models.User(
        username=user.username,
        password=user.password,
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
    user = db.execute(text(f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'")).fetchone()
    
    if not user:
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
    
    user = db.execute(text(f"SELECT * FROM users WHERE username = '{code['username']}'")).fetchone()
    
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