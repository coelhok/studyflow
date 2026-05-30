from __future__ import annotations

from app.database import fetch_all


def search_chunks(notebook_id: int, query: str, document_ids: list[int] | None = None, limit: int = 5):
    words = [w.lower() for w in query.split() if len(w) > 3]
    params: list = [notebook_id]
    doc_filter = ""
    if document_ids:
        placeholders = ",".join(["?"] * len(document_ids))
        doc_filter = f" AND document_chunks.document_id IN ({placeholders})"
        params.extend(document_ids)

    # Build 4.1: busca em uma janela controlada de chunks. O chat nunca puxa o PDF inteiro.
    chunks = fetch_all(
        f"""
        SELECT document_chunks.id, document_chunks.document_id, document_chunks.notebook_id,
               document_chunks.content, document_chunks.page_number, document_chunks.chunk_index,
               documents.filename
        FROM document_chunks
        JOIN documents ON documents.id = document_chunks.document_id
        WHERE document_chunks.notebook_id = ? {doc_filter}
        ORDER BY document_chunks.id DESC
        LIMIT 80
        """,
        params,
    )
    scored = []
    for c in chunks:
        text = c["content"].lower()
        score = sum(1 for w in words if w in text)
        scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [c for score, c in scored[:limit] if score > 0] or [c for _, c in scored[:limit]]
    return selected
