from fastapi import APIRouter
from pydantic import BaseModel
from app.database import execute, fetch_all

router = APIRouter()

class NotebookIn(BaseModel):
    user_id: int = 1
    title: str = "Novo notebook"

@router.get("")
def list_notebooks(user_id: int = 1):
    return fetch_all("SELECT * FROM notebooks WHERE user_id = ? ORDER BY updated_at DESC", (user_id,))

@router.post("")
def create_notebook(data: NotebookIn):
    notebook_id = execute("INSERT INTO notebooks (user_id, title) VALUES (?, ?)", (data.user_id, data.title), returning=True)
    return {"id": notebook_id, "title": data.title}
