import sqlite3
from pathlib import Path
from typing import Any, Iterable

from app.config import settings

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # psycopg só é necessário em produção com PostgreSQL/Supabase
    psycopg = None
    dict_row = None

BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_PATH = BASE_DIR / "studyflow.db"


def is_postgres() -> bool:
    return settings.database_url.startswith(("postgres://", "postgresql://"))


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS notebooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    notebook_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    storage_path TEXT,
    status TEXT DEFAULT 'processed',
    file_size INTEGER DEFAULT 0,
    text_char_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    notebook_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER DEFAULT 1,
    chunk_index INTEGER NOT NULL,
    embedding TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notebook_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS generated_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notebook_id INTEGER NOT NULL,
    document_id INTEGER,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS agent_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    memory_key TEXT NOT NULL,
    memory_value TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS notebooks (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notebook_id BIGINT NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    storage_path TEXT,
    status TEXT DEFAULT 'processed',
    file_size BIGINT DEFAULT 0,
    text_char_count BIGINT DEFAULT 0,
    chunk_count BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    notebook_id BIGINT NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    page_number INTEGER DEFAULT 1,
    chunk_index INTEGER NOT NULL,
    embedding TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGSERIAL PRIMARY KEY,
    notebook_id BIGINT NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS generated_materials (
    id BIGSERIAL PRIMARY KEY,
    notebook_id BIGINT NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    document_id BIGINT REFERENCES documents(id) ON DELETE SET NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS agent_memory (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_key TEXT NOT NULL,
    memory_value TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""


def _connect():
    if is_postgres():
        if psycopg is None:
            raise RuntimeError("psycopg não instalado. Rode: pip install -r requirements.txt")
        return psycopg.connect(normalize_database_url(settings.database_url), row_factory=dict_row)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def q(sql: str) -> str:
    return sql.replace("?", "%s") if is_postgres() else sql


def fetch_all(sql: str, params: Iterable[Any] = ()) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(q(sql), tuple(params)).fetchall()
        return [dict(r) for r in rows]


def fetch_one(sql: str, params: Iterable[Any] = ()) -> dict | None:
    with _connect() as conn:
        row = conn.execute(q(sql), tuple(params)).fetchone()
        return dict(row) if row else None


def execute(sql: str, params: Iterable[Any] = (), returning: bool = False) -> int | None:
    with _connect() as conn:
        final_sql = q(sql)
        if is_postgres() and returning and "RETURNING" not in final_sql.upper():
            final_sql += " RETURNING id"
        cur = conn.execute(final_sql, tuple(params))
        new_id = None
        if returning:
            if is_postgres():
                row = cur.fetchone()
                new_id = int(row["id"] if isinstance(row, dict) else row[0])
            else:
                new_id = int(cur.lastrowid)
        conn.commit()
        return new_id


def execute_many(sql: str, rows: list[Iterable[Any]]) -> None:
    if not rows:
        return
    with _connect() as conn:
        if is_postgres():
            with conn.cursor() as cur:
                cur.executemany(q(sql), [tuple(r) for r in rows])
        else:
            conn.executemany(sql, [tuple(r) for r in rows])
        conn.commit()



def _ensure_document_metadata_columns() -> None:
    """Garante colunas novas mesmo quando o SQLite antigo já existe."""
    columns = {
        "file_size": "INTEGER DEFAULT 0",
        "text_char_count": "INTEGER DEFAULT 0",
        "chunk_count": "INTEGER DEFAULT 0",
    }
    with _connect() as conn:
        if is_postgres():
            existing_rows = conn.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'documents'
            """).fetchall()
            existing = {r["column_name"] if isinstance(r, dict) else r[0] for r in existing_rows}
        else:
            existing_rows = conn.execute("PRAGMA table_info(documents)").fetchall()
            existing = {r["name"] if isinstance(r, sqlite3.Row) else r[1] for r in existing_rows}
        for name, definition in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE documents ADD COLUMN {name} {definition}")
        conn.commit()

def init_db() -> None:
    with _connect() as conn:
        if is_postgres():
            for statement in [s.strip() for s in POSTGRES_SCHEMA.split(';') if s.strip()]:
                conn.execute(statement)
        else:
            conn.executescript(SQLITE_SCHEMA)
        conn.commit()

    _ensure_document_metadata_columns()

    # Usuário de demonstração para o sistema abrir sem cadastro durante testes.
    existing = fetch_one("SELECT id FROM users WHERE id = ?", (1,))
    if not existing:
        execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Kevin", "demo@studyflow.local", "demo"),
        )
    has_notebook = fetch_one("SELECT id FROM notebooks WHERE user_id = ? LIMIT 1", (1,))
    if not has_notebook:
        execute("INSERT INTO notebooks (user_id, title) VALUES (?, ?)", (1, "Aprendizado Profundo"))
