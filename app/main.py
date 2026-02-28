from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Admin
from .schemas import AdminCreate, LoginRequest, TokenResponse, AdminOut
from .auth import hash_password, verify_password, create_access_token, decode_token
from jose import JWTError

app = FastAPI(title="POS Server")

# kreye tab yo otomatikman (pi fasil pou kòmanse)
Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@app.get("/")
def root():
    return {"status": "ok", "message": "POS Server is running"}

# ---- BOOTSTRAP ADMIN (fè 1 fwa, epi ou ka retire route sa pita) ----
@app.post("/auth/bootstrap-admin", response_model=AdminOut, status_code=201)
def bootstrap_admin(data: AdminCreate, db: Session = Depends(get_db)):
    exists = db.query(Admin).filter(Admin.username == data.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="Admin already exists")

    admin = Admin(
        username=data.username,
        password_hash=hash_password(data.password),
        role="admin",
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

# ---- LOGIN ----
@app.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == data.username).first()
    if not admin or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")

    if not verify_password(data.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")

    token = create_access_token(subject=str(admin.id), role=admin.role)
    return TokenResponse(access_token=token)

# ---- DEPENDENCY: current admin ----
def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Admin:
    try:
        payload = decode_token(token)
        admin_id = int(payload.get("sub", "0"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="Invalid token")
    return admin

# ---- TEST PROTECTED ROUTE ----
@app.get("/auth/me", response_model=AdminOut)
def me(current: Admin = Depends(get_current_admin)):
    return current