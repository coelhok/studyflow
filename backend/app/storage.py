from pathlib import Path
from app.config import settings


def upload_to_supabase_storage(local_path: Path, storage_name: str) -> str | None:
    """Envia arquivo para Supabase Storage quando as variáveis estão configuradas.
    Em desenvolvimento local, retorna None e o sistema usa o arquivo local.
    """
    if not settings.supabase_url or not settings.supabase_service_key:
        return None
    try:
        from supabase import create_client
        client = create_client(settings.supabase_url, settings.supabase_service_key)
        data = local_path.read_bytes()
        client.storage.from_(settings.supabase_storage_bucket).upload(
            path=storage_name,
            file=data,
            file_options={"upsert": "true"},
        )
        return storage_name
    except Exception as exc:
        print(f"[storage] Supabase Storage indisponível: {exc}")
        return None
