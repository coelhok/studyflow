import hashlib
import secrets
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.database import execute, fetch_one

router = APIRouter()

class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

@router.post("/register")
def register(data: RegisterIn):
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="A senha precisa ter pelo menos 6 caracteres.")
    existing = fetch_one("SELECT id FROM users WHERE email = ?", (data.email.lower(),))
    if existing:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    user_id = execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (data.name.strip(), data.email.lower(), hash_password(data.password)),
        returning=True,
    )
    notebook_id = execute(
        "INSERT INTO notebooks (user_id, title) VALUES (?, ?)",
        (user_id, "Meu primeiro notebook"),
        returning=True,
    )
    token = f"dev-{user_id}-{secrets.token_hex(8)}"
    return {"token": token, "user": {"id": user_id, "name": data.name, "email": data.email}, "default_notebook_id": notebook_id}

@router.post("/login")
def login(data: LoginIn):
    user = fetch_one("SELECT * FROM users WHERE email = ?", (data.email.lower(),))
    if not user or user["password_hash"] != hash_password(data.password):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    token = f"dev-{user['id']}-{secrets.token_hex(8)}"
    return {"token": token, "user": {"id": user["id"], "name": user["name"], "email": user["email"]}}
