from pydantic import BaseModel, Field

class Msg(BaseModel):
    status: str = "ok"
    message: str

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool

class BootstrapAdminIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=200)

class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CreateCashierIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=200)