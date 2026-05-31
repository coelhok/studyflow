# StudyFlow PDF AI - Build 5.2

Build focada em corrigir regressões da 5.1:

- Sanitização de nomes para Supabase Storage.
- Correção de seleção obsoleta após exclusão de documentos.
- Limpeza de IDs inválidos antes do chat.
- Endpoint `/api/health/llm/test` para testar chamada real do LLM.
- Mantém agente real com Groq, RAG e multi-função.

> Copie seu `.env` real para `backend/.env` antes de rodar. Nunca suba `.env` para o GitHub.

---

# StudyFlow PDF AI — Build 5.1

Aplicação web com FastAPI + HTML/CSS/JS, Supabase PostgreSQL/Storage e agente de IA com RAG.

## Rodar localmente

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Acesse:

```txt
http://127.0.0.1:8000
```

## Variáveis obrigatórias

Copie seu `.env` da Build 4.4 para `backend/.env`.

Campos principais:

```env
DATABASE_URL=postgresql://...
LLM_PROVIDER=groq
GROQ_API_KEY=...
GROQ_MODEL=llama-3.3-70b-versatile
SUPABASE_URL=https://...supabase.co
SUPABASE_SERVICE_KEY=...
SUPABASE_BUCKET=documents
```

Fallback opcional:

```env
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-1.5-flash
```

## Health checks

```txt
/api/health/database
/api/health/storage
/api/health/llm
```

## O que mudou na Build 5.1

- RAG mais inteligente: não pega só os chunks iniciais.
- Seleção de contexto por relevância, estrutura e amostragem distribuída.
- Fallback local seguro quando Groq falha, sem despejar chunks crus.
- Suporte melhor a multi-função: resumo, quiz, plano, fluxograma, revisão, flashcards e comparação.
- Prompt mais rígido contra alucinação e prompt injection.
- Cliente LLM com headers melhores e fallback opcional Gemini/OpenAI.
- Testes documentados em `docs/testes_agente_build5_1.md`.

## Observação sobre Groq HTTP 403/1010

Se o Groq retornar `HTTP 403: error code 1010`, o agente mantém resposta segura baseada nos chunks. Para testar IA real, tente:

1. Trocar para outro modelo Groq.
2. Testar no Railway.
3. Configurar `GEMINI_API_KEY` como fallback.

O agente não deve inventar informação fora dos documentos mesmo quando o LLM falhar.

## Build 5.4

Correções de lapidação:
- Fluxograma Mermaid sem card duplicado.
- Prompt de fluxograma mais direto e fiel ao documento.
- Exclusão de documentos com proteção contra clique duplo.
- DELETE idempotente no backend.
- Indicador visual de fonte ativa quando há fallback para documento único.

## Build 6 — autenticação e isolamento por usuário

A partir da Build 6, o sistema não usa mais `user_id=1` no frontend. O usuário faz login/cadastro, recebe um token assinado e todas as rotas principais usam o usuário autenticado.

Rotas principais:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `GET /api/notebooks`
- `POST /api/notebooks`
- `GET /api/documents`
- `POST /api/documents/upload`
- `DELETE /api/documents/{id}`
- `POST /api/chat/stream`

Antes do deploy, configure no `.env`:

```env
JWT_SECRET=troque_por_uma_chave_forte
DATABASE_URL=postgresql://...
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
SUPABASE_BUCKET=documents
LLM_PROVIDER=groq
GROQ_API_KEY=...
```
