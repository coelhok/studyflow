# Arquitetura - StudyFlow PDF AI

A Build 3 usa uma arquitetura monolítica leve: o FastAPI entrega a interface e também expõe as rotas da API.

## Camadas

1. **Interface Web**: HTML, CSS e JavaScript em `backend/templates` e `backend/static`.
2. **API FastAPI**: rotas em `/api` para autenticação, notebooks, documentos e chat.
3. **Processamento de arquivos**: leitura de PDF, DOCX e TXT.
4. **RAG inicial**: chunks salvos no banco e busca textual simples.
5. **Persistência**: SQLite local ou Supabase PostgreSQL em produção.
6. **Storage**: Supabase Storage quando configurado.

## Produção

O Railway executa o FastAPI. O Supabase fornece banco PostgreSQL e Storage.
