from __future__ import annotations

import json
import time
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agent import build_agent_answer, stream_steps
from app.database import execute, fetch_all

router = APIRouter()


class ChatIn(BaseModel):
    user_id: int = 1
    notebook_id: int = 1
    message: str
    selected_document_ids: list[int] = Field(default_factory=list)


def _log(message: str) -> None:
    print(f"[API][CHAT] {message}", flush=True)


@router.get("/history/{notebook_id}")
def history(notebook_id: int):
    _log(f"Carregando histórico do notebook_id={notebook_id}")
    return fetch_all("SELECT * FROM chat_messages WHERE notebook_id = ? ORDER BY id ASC", (notebook_id,))


@router.post("/message")
def chat_message(data: ChatIn):
    _log(f"Mensagem recebida notebook_id={data.notebook_id} user_id={data.user_id}")
    _log(f"Documentos selecionados: {data.selected_document_ids}")
    result = build_agent_answer(data.notebook_id, data.message, data.selected_document_ids)
    execute(
        "INSERT INTO chat_messages (notebook_id, user_id, role, content) VALUES (?, ?, ?, ?)",
        (data.notebook_id, data.user_id, "user", data.message),
    )
    execute(
        "INSERT INTO chat_messages (notebook_id, user_id, role, content) VALUES (?, ?, ?, ?)",
        (data.notebook_id, data.user_id, "assistant", result["answer"]),
    )
    _log("Resposta montada e salva no histórico")
    return result


@router.post("/stream")
def chat_stream(data: ChatIn):
    _log(f"STREAM iniciado notebook_id={data.notebook_id} user_id={data.user_id}")
    _log(f"Mensagem: {data.message!r}")
    _log(f"Documentos selecionados: {data.selected_document_ids}")
    result = build_agent_answer(data.notebook_id, data.message, data.selected_document_ids)

    execute(
        "INSERT INTO chat_messages (notebook_id, user_id, role, content) VALUES (?, ?, ?, ?)",
        (data.notebook_id, data.user_id, "user", data.message),
    )
    execute(
        "INSERT INTO chat_messages (notebook_id, user_id, role, content) VALUES (?, ?, ?, ?)",
        (data.notebook_id, data.user_id, "assistant", result["answer"]),
    )

    def event_stream():
        for step in stream_steps(result):
            payload = {"type": "status", "message": step}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            time.sleep(0.22)

        answer = result["answer"]
        # Envia em pedaços para dar sensação real de streaming sem quebrar markdown.
        chunk_size = 48
        for idx in range(0, len(answer), chunk_size):
            payload = {"type": "content", "message": answer[idx: idx + chunk_size]}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            time.sleep(0.035)

        yield f"data: {json.dumps({'type': 'done', 'message': '✅ Finalizado.'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
