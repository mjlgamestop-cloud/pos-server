from fastapi import FastAPI
from .db import engine
from .models import User  # noqa
from .db import Base
from .routes.auth import router as auth_router
from .routes.users import router as users_router

app = FastAPI(title="POS Server", version="1.0.0")

@app.on_event("startup")
def on_startup():
    # Pou fasil: kreye tables otomatikman
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"status": "ok", "message": "POS Server is running"}

app.include_router(auth_router)
app.include_router(users_router)