from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from .db import Base, engine, get_db
from .models import User
from .schemas import (
    BootstrapAdminRequest,
    CashierCreateRequest,
    LoginRequest,
    TokenResponse,
    UserOut,
)
from .auth import hash_password, verify_password, create_access_token, decode_token

app = FastAPI(title="POS Server")

# Kreye tab yo otomatikman (pi fasil pou kòmanse)
Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@app.get("/")
def root():
    return {"status": "ok", "message": "POS Server is running"}


# --------------------------
# 1) BOOTSTRAP ADMIN (fè 1 fwa)
# --------------------------
@app.post("/auth/bootstrap-admin", response_model=UserOut, status_code=201)
def bootstrap_admin(data: BootstrapAdminRequest, db: Session = Depends(get_db)):
    # Si gen admin deja, pa kreye ankò
    exists_admin = db.query(User).filter(User.role == "admin").first()
    if exists_admin:
        raise HTTPException(status_code=400, detail="Admin already exists")

    # Username pa dwe egziste
    exists_username = db.query(User).filter(User.username == data.username).first()
    if exists_username:
        raise HTTPException(status_code=400, detail="Username already exists")

    admin = User(
        username=data.username,
        password_hash=hash_password(data.password),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


# --------------------------
# 2) LOGIN -> JWT TOKEN
# --------------------------
@app.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")

    token = create_access_token(subject=str(user.id), role=user.role)
    return TokenResponse(access_token=token)


# --------------------------
# 3) CURRENT USER (token required)
# --------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub", "0"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def require_admin(current: User = Depends(get_current_user)) -> User:
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return current


@app.get("/auth/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current


# --------------------------
# 4) CREATE CASHIER (admin only)
# --------------------------
@app.post("/users/cashiers", response_model=UserOut, status_code=201)
def create_cashier(
    data: CashierCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    exists = db.query(User).filter(User.username == data.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="Username already exists")

    cashier = User(
        username=data.username,
        password_hash=hash_password(data.password),
        role="cashier",
        is_active=True,
    )
    db.add(cashier)
    db.commit()
    db.refresh(cashier)
    return cashier