from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..deps import get_db, get_current_user
from ..models import User
from ..schemas import BootstrapAdminIn, LoginIn, TokenOut, Msg, UserOut
from ..security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/bootstrap-admin", response_model=Msg)
def bootstrap_admin(payload: BootstrapAdminIn, db: Session = Depends(get_db)):
    # Si deja gen admin, pa kite repete
    existing_admin = db.query(User).filter(User.role == "admin").first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists")

    # Pa kite username repete
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    admin = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    return Msg(message="Admin created successfully")

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")

    token = create_access_token(subject=user.username, role=user.role)
    return TokenOut(access_token=token)

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(id=user.id, username=user.username, role=user.role, is_active=user.is_active)