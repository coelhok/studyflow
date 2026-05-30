from pathlib import Path
from time import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.database import execute, execute_many, fetch_all
from app.file_reader import read_file, chunk_text
from app.storage import upload_to_supabase_storage

router = APIRouter()
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED = {".pdf", ".docx", ".txt"}
MAX_UPLOAD_MB = 15
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024


def _log(message: str) -> None:
    print(f"[API][UPLOAD] {message}", flush=True)


def _public_document_select() -> str:
    # Build 4.1: listagem retorna só metadados. Nada de texto/chunks no frontend.
    return """
        SELECT
            documents.id,
            documents.user_id,
            documents.notebook_id,
            documents.filename,
            documents.file_type,
            documents.storage_path,
            documents.status,
            documents.file_size,
            documents.text_char_count,
            documents.chunk_count,
            documents.created_at
        FROM documents
    """


@router.get("")
def list_documents(user_id: int = 1, notebook_id: int | None = None):
    _log(f"Listando metadados user_id={user_id} notebook_id={notebook_id}")
    query = _public_document_select() + " WHERE documents.user_id = ?"
    params: list = [user_id]
    if notebook_id:
        query += " AND documents.notebook_id = ?"
        params.append(notebook_id)
    query += " ORDER BY documents.created_at DESC"
    return fetch_all(query, params)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_id: int = Form(1),
    notebook_id: int = Form(1),
):
    _log(f"Recebendo arquivo filename={file.filename!r} user_id={user_id} notebook_id={notebook_id}")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        _log(f"Tipo recusado: {suffix}")
        raise HTTPException(status_code=400, detail="Envie apenas PDF, DOCX ou TXT.")

    safe_name = Path(file.filename or "arquivo").name
    unique_name = f"{int(time())}_{safe_name}"
    target = UPLOAD_DIR / unique_name

    try:
        content = await file.read()
        file_size = len(content)
        _log(f"Bytes recebidos: {file_size}")
        if file_size > MAX_UPLOAD_BYTES:
            _log(f"Arquivo recusado por tamanho: {file_size} bytes")
            raise HTTPException(status_code=413, detail=f"Arquivo muito grande. Limite atual: {MAX_UPLOAD_MB} MB.")

        target.write_bytes(content)
        _log(f"Arquivo salvo localmente em: {target}")

        text = read_file(target)
        text_len = len(text or "")
        _log(f"Caracteres extraídos: {text_len}")

        chunks = chunk_text(text, size=900, overlap=120)
        chunk_count = len(chunks)
        _log(f"Chunks gerados: {chunk_count}")

        if text.startswith("[Erro ao ler"):
            status = "error"
            chunks = [text]
            chunk_count = 1
        elif not chunks:
            status = "empty"
            chunks = ["[Nenhum texto útil foi extraído deste arquivo.]"]
            chunk_count = 1
        else:
            status = "processed"

        storage_path = upload_to_supabase_storage(target, f"users/{user_id}/notebooks/{notebook_id}/{unique_name}")
        _log(f"Storage path: {storage_path or 'local/fallback'}")

        doc_id = execute(
            """
            INSERT INTO documents
            (user_id, notebook_id, filename, file_type, file_path, storage_path, status, file_size, text_char_count, chunk_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, notebook_id, safe_name, suffix.replace('.', ''), str(target), storage_path, status, file_size, text_len, chunk_count),
            returning=True,
        )
        execute_many(
            "INSERT INTO document_chunks (document_id, notebook_id, content, page_number, chunk_index) VALUES (?, ?, ?, ?, ?)",
            [(doc_id, notebook_id, chunk, 1, idx) for idx, chunk in enumerate(chunks)],
        )
        _log(f"Documento salvo no banco id={doc_id} status={status} chunks={chunk_count}")
        return {
            "id": doc_id,
            "filename": safe_name,
            "file_type": suffix.replace('.', ''),
            "file_size": file_size,
            "text_char_count": text_len,
            "chunk_count": chunk_count,
            "chunks": chunk_count,
            "status": status,
            "storage_path": storage_path,
        }
    except HTTPException:
        raise
    except Exception as exc:
        _log(f"ERRO: {exc}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {exc}")
