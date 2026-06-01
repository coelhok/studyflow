from __future__ import annotations

import json
import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agent import build_agent_answer, stream_steps
from app.auth import get_current_user_id
from app.database import execute, fetch_all, fetch_one
from app.app_logger import log as app_log

router = APIRouter()


class ChatIn(BaseModel):
    notebook_id: str
    message: str
    selected_document_ids: list = Field(default_factory=list)


class QuizAttemptIn(BaseModel):
    notebook_id: str
    document_ids: list = Field(default_factory=list)
    title: str = "Questionário"
    score: int
    total_questions: int
    answered: int
    answers: list | dict = Field(default_factory=list)


def _log(message: str) -> None:
    app_log("API][CHAT", message)


def _ensure_notebook(notebook_id, user_id):
    nb = fetch_one("SELECT id FROM notebooks WHERE id = ? AND user_id = ?", (notebook_id, user_id))
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook não encontrado para este usuário.")
    return nb


def _valid_document_ids(notebook_id, user_id, ids: list) -> list:
    ids = [str(x) for x in (ids or []) if str(x).strip()]
    if not ids:
        return []
    placeholders = ",".join(["?"] * len(ids))
    rows = fetch_all(
        f"SELECT id FROM documents WHERE notebook_id = ? AND user_id = ? AND status = 'processed' AND id IN ({placeholders})",
        [notebook_id, user_id, *ids],
    )
    valid = [str(r['id']) for r in rows]
    invalid = [x for x in ids if x not in valid]
    if invalid:
        _log(f"IDs de documentos ignorados porque não pertencem ao usuário/notebook ou foram removidos: {invalid}")
    return valid


def _save_message(notebook_id, user_id, role: str, content: str) -> None:
    execute(
        "INSERT INTO chat_messages (notebook_id, user_id, role, content) VALUES (?, ?, ?, ?)",
        (notebook_id, user_id, role, content),
    )


@router.get("/history/{notebook_id}")
def history(notebook_id: str, request: Request):
    user_id = get_current_user_id(request)
    _ensure_notebook(notebook_id, user_id)
    _log(f"Carregando histórico do notebook_id={notebook_id} user_id={user_id}")
    return fetch_all(
        "SELECT * FROM chat_messages WHERE notebook_id = ? AND user_id = ? ORDER BY created_at ASC",
        (notebook_id, user_id),
    )


@router.post("/quiz-attempt")
def save_quiz_attempt(data: QuizAttemptIn, request: Request):
    user_id = get_current_user_id(request)
    _ensure_notebook(data.notebook_id, user_id)
    valid_docs = _valid_document_ids(data.notebook_id, user_id, data.document_ids)
    total = max(0, int(data.total_questions or 0))
    score = max(0, min(int(data.score or 0), total))
    answered = max(0, min(int(data.answered or 0), total))
    execute(
        """
        INSERT INTO quiz_attempts (user_id, notebook_id, document_ids, title, score, total_questions, answered, answers)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            data.notebook_id,
            json.dumps(valid_docs, ensure_ascii=False),
            (data.title or "Questionário")[:160],
            score,
            total,
            answered,
            json.dumps(data.answers, ensure_ascii=False),
        ),
    )
    _log(f"Quiz salvo score={score}/{total} answered={answered} notebook_id={data.notebook_id}")
    return {"ok": True, "score": score, "total_questions": total, "answered": answered}


@router.post("/message")
def chat_message(data: ChatIn, request: Request):
    user_id = get_current_user_id(request)
    _ensure_notebook(data.notebook_id, user_id)
    selected_ids = _valid_document_ids(data.notebook_id, user_id, data.selected_document_ids)
    _log(f"Mensagem recebida notebook_id={data.notebook_id} user_id={user_id}")
    _log(f"Documentos selecionados válidos: {selected_ids}")
    _save_message(data.notebook_id, user_id, "user", data.message)
    result = build_agent_answer(data.notebook_id, data.message, selected_ids, user_id=user_id)
    _save_message(data.notebook_id, user_id, "assistant", result["answer"])
    _log("Resposta real/multi-função montada e salva no histórico")
    return result


@router.post("/stream")
def chat_stream(data: ChatIn, request: Request):
    user_id = get_current_user_id(request)
    _ensure_notebook(data.notebook_id, user_id)
    selected_ids = _valid_document_ids(data.notebook_id, user_id, data.selected_document_ids)
    _log(f"STREAM iniciado notebook_id={data.notebook_id} user_id={user_id}")
    _log(f"Mensagem: {data.message!r}")
    _log(f"Documentos selecionados válidos: {selected_ids}")

    def event_stream():
        try:
            for step in stream_steps(pre=True):
                payload = {"type": "status", "message": step}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                time.sleep(0.18)

            _save_message(data.notebook_id, user_id, "user", data.message)
            result = build_agent_answer(data.notebook_id, data.message, selected_ids, user_id=user_id)
            _save_message(data.notebook_id, user_id, "assistant", result["answer"])

            for step in stream_steps(result):
                payload = {"type": "status", "message": step}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                time.sleep(0.18)

            answer = result["answer"]
            chunk_size = 54
            for idx in range(0, len(answer), chunk_size):
                payload = {"type": "content", "message": answer[idx: idx + chunk_size]}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                time.sleep(0.018)

            yield f"data: {json.dumps({'type': 'done', 'message': '✅ Finalizado.'}, ensure_ascii=False)}\n\n"
        except Exception as exc:
            _log(f"STREAM erro: {exc}")
            payload = {
                "type": "content",
                "message": "Não consegui concluir a resposta por erro interno do agente. Veja o terminal do FastAPI para detalhes.",
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'message': '⚠️ Finalizado com erro.'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
