from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.database import fetch_all
from app.rag import search_chunks


@dataclass
class AgentPlan:
    tasks: list[str]
    mode: str
    friendly_mode: str


TASK_LABELS = {
    "summary": "resumo",
    "quiz": "questionário",
    "flowchart": "fluxograma",
    "study_plan": "plano de estudo",
    "flashcards": "flashcards",
    "quick_review": "revisão rápida",
    "compare_docs": "comparação de documentos",
    "explain_simple": "explicação simples",
    "free_question": "resposta com base nos documentos",
}


def _log(message: str) -> None:
    print(f"[AGENT] {message}", flush=True)


def detect_tasks(message: str) -> list[str]:
    msg = message.lower()
    tasks: list[str] = []

    checks = [
        ("summary", ["resumo", "resuma", "resumir", "sintese", "síntese"]),
        ("quiz", ["question", "quiz", "pergunta", "questões", "questoes", "questionário", "questionario"]),
        ("flowchart", ["fluxograma", "fluxo", "mermaid", "diagrama"]),
        ("study_plan", ["plano", "cronograma", "rotina de estudo", "estudo semanal"]),
        ("flashcards", ["flashcard", "cartão", "cartao"]),
        ("quick_review", ["revisão rápida", "revisao rapida", "revisar", "revisão", "revisao"]),
        ("compare_docs", ["comparar", "compare", "diferença", "diferenças", "diferencas", "semelhanças"]),
        ("explain_simple", ["iniciante", "simples", "explique", "explica", "fácil", "facil"]),
    ]

    for task, keywords in checks:
        if any(k in msg for k in keywords):
            tasks.append(task)

    if not tasks:
        tasks.append("free_question")

    # Remove duplicados mantendo ordem.
    unique: list[str] = []
    for task in tasks:
        if task not in unique:
            unique.append(task)
    return unique


def get_documents(notebook_id: int, selected_document_ids: Iterable[int] | None = None) -> list[dict]:
    selected = [int(x) for x in (selected_document_ids or []) if str(x).strip()]
    if selected:
        placeholders = ",".join(["?"] * len(selected))
        docs = fetch_all(
            f"""
            SELECT * FROM documents
            WHERE notebook_id = ? AND id IN ({placeholders})
            ORDER BY created_at DESC
            """,
            [notebook_id, *selected],
        )
        return docs

    return fetch_all(
        "SELECT * FROM documents WHERE notebook_id = ? ORDER BY created_at DESC",
        (notebook_id,),
    )


def build_plan(message: str, docs: list[dict]) -> AgentPlan:
    tasks = detect_tasks(message)
    if len(docs) == 0:
        mode = "sem_documento"
        friendly = "aguardando fonte"
    elif len(docs) == 1:
        mode = "single_document"
        friendly = "análise individual"
    else:
        mode = "multi_document"
        friendly = "análise multi-documento"
    return AgentPlan(tasks=tasks, mode=mode, friendly_mode=friendly)


def build_agent_answer(
    notebook_id: int,
    message: str,
    selected_document_ids: list[int] | None = None,
) -> dict:
    _log(f"Mensagem recebida: {message!r}")
    docs = get_documents(notebook_id, selected_document_ids)
    _log(f"Documentos encontrados/selecionados: {len(docs)}")
    plan = build_plan(message, docs)
    _log(f"Tarefas detectadas: {plan.tasks}")
    _log(f"Modo escolhido: {plan.mode}")

    if not docs:
        answer = (
            "Entendi seu pedido, mas ainda não encontrei nenhum documento selecionado neste notebook.\n\n"
            "Para eu agir como agente de estudos de verdade, envie ou selecione pelo menos um PDF, DOCX ou TXT. "
            "Assim eu consigo analisar a fonte e preparar a resposta com base no conteúdo real do arquivo."
        )
        return {
            "answer": answer,
            "tasks": plan.tasks,
            "mode": plan.mode,
            "documents": [],
            "context_preview": "",
        }

    doc_ids = [int(d["id"]) for d in docs]
    chunks = search_chunks(notebook_id, message, document_ids=doc_ids, limit=6)
    context = "\n\n".join(f"Fonte: {c['filename']}\n{c['content']}" for c in chunks)
    _log(f"Chunks usados no contexto: {len(chunks)}")

    task_names = ", ".join(TASK_LABELS.get(t, t) for t in plan.tasks)
    doc_lines = "\n".join(f"- {d['filename']} ({d.get('file_type', 'arquivo').upper()})" for d in docs)

    if len(plan.tasks) > 1:
        action_text = (
            "Você pediu mais de uma ação. Vou tratar isso como uma solicitação multi-função e executar em ordem lógica."
        )
    else:
        action_text = "Vou tratar seu pedido como uma tarefa principal do agente."

    preview = context[:900].strip()
    if not preview:
        preview = "Não consegui recuperar trechos úteis ainda. O arquivo pode estar vazio, protegido ou mal processado."

    # Build 4: resposta comportamental do agente. As ferramentas completas entram na Build 5.
    answer = f"""Perfeito. Vou trabalhar como agente de estudos, não como chatbot comum.

**Modo detectado:** {plan.friendly_mode}  
**Tarefas identificadas:** {task_names}

**Fontes que vou usar:**
{doc_lines}

{action_text}

**O que eu já consegui verificar agora:**
{preview}

**Próximo passo do agente:**
Na próxima etapa, vou transformar esse planejamento em ferramentas completas: resumo real, questionário, fluxograma, plano de estudo, flashcards, comparação entre PDFs e revisão rápida.

Por enquanto, a Build 4 está validando o comportamento do agente: seleção de fontes, modo multi-documento, detecção de intenção, status em tempo real e logs para depuração."""

    return {
        "answer": answer,
        "tasks": plan.tasks,
        "mode": plan.mode,
        "documents": [{"id": d["id"], "filename": d["filename"], "status": d.get("status", "processed")} for d in docs],
        "context_preview": preview,
    }


def stream_steps(result: dict) -> list[str]:
    docs = result.get("documents") or []
    tasks = result.get("tasks") or []
    mode = result.get("mode") or "desconhecido"
    return [
        "🔎 Verificando fontes selecionadas...",
        f"📄 Documentos encontrados: {len(docs)}.",
        f"🧭 Modo de análise: {mode}.",
        f"🧠 Tarefas detectadas: {', '.join(TASK_LABELS.get(t, t) for t in tasks)}.",
        "🛠️ Preparando plano de ação do agente...",
        "✍️ Montando resposta organizada...",
    ]
