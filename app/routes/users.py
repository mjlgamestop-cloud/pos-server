from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..deps import get_db, require_admin
from ..models import User
from ..schemas import CreateCashierIn, Msg, UserOut
from ..security import hash_password

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/cashiers", response_model=UserOut)
def create_cashier(
    payload: CreateCashierIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    cashier = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role="cashier",
        is_active=True,
    )
    db.add(cashier)
    db.commit()
    db.refresh(cashier)
    return UserOut(id=cashier.id, username=cashier.username, role=cashier.role, is_active=cashier.is_active)

@router.get("/cashiers", response_model=list[UserOut])
def list_cashiers(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    cashiers = db.query(User).filter(User.role == "cashier").order_by(User.id.desc()).all()
    return [UserOut(id=u.id, username=u.username, role=u.role, is_active=u.is_active) for u in cashiers]