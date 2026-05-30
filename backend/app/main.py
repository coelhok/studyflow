from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth import router as auth_router
from app.documents import router as documents_router
from app.chat import router as chat_router
from app.notebooks import router as notebooks_router
from app.database import init_db
from app.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title=settings.app_name, version="0.4.0")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True, "service": settings.app_name, "version": "0.4.0"}

# Páginas HTML servidas pelo próprio FastAPI. Assim o sistema inteiro roda em uma porta só.
@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/notebook")
def notebook_page(request: Request):
    return templates.TemplateResponse("notebook.html", {"request": request})

@app.get("/history")
def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

@app.get("/settings")
def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# API oficial em /api para produção/deploy.
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(notebooks_router, prefix="/api/notebooks", tags=["notebooks"])
app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

# Rotas antigas mantidas por compatibilidade com testes da Build 2.
app.include_router(auth_router, prefix="/auth", tags=["legacy-auth"])
app.include_router(notebooks_router, prefix="/notebooks", tags=["legacy-notebooks"])
app.include_router(documents_router, prefix="/documents", tags=["legacy-documents"])
app.include_router(chat_router, prefix="/chat", tags=["legacy-chat"])
