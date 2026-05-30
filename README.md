# StudyFlow PDF AI - Build 4.1

Aplicação web com **FastAPI + HTML/CSS/JavaScript** para leitura de PDF, DOCX e TXT com agente de IA, RAG inicial, histórico e materiais de estudo.

Nesta build, o sistema foi ajustado para rodar como **uma aplicação única**, pronta para deploy no Railway:

- FastAPI serve as páginas HTML.
- CSS/JS ficam em `/static`.
- APIs ficam em `/api`.
- O app roda em uma única porta.
- Estrutura preparada para Railway + Supabase PostgreSQL + Supabase Storage.

## Arquitetura da Build 3

```txt
StudyFlow PDF AI
├── Railway
│   └── FastAPI
│       ├── páginas HTML
│       ├── arquivos CSS/JS
│       ├── API REST
│       ├── upload de documentos
│       ├── leitura PDF/DOCX/TXT
│       ├── RAG inicial
│       └── agente de IA em modo mock
│
└── Supabase
    ├── PostgreSQL
    └── Storage
```

## Rotas da aplicação

```txt
/            Página inicial
/login       Login
/register    Cadastro
/dashboard   Dashboard
/notebook    Agente de IA
/history     Histórico
/settings    Configurações
/docs        Swagger/FastAPI
/health      Status da API
```

## Rotas da API

```txt
/api/auth/register
/api/auth/login
/api/notebooks
/api/documents
/api/documents/upload
/api/chat/message
/api/chat/stream
/api/chat/history/{notebook_id}
```

## Rodar localmente

Entre na pasta do backend:

```bash
cd backend
```

Crie e ative o ambiente virtual:

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Rode o servidor:

```bash
uvicorn app.main:app --reload
```

Acesse:

```txt
http://127.0.0.1:8000
```

Agora não precisa mais rodar servidor separado para o frontend.

## Variáveis de ambiente

Copie o arquivo:

```bash
copy .env.example .env
```

Localmente pode usar SQLite:

```env
DATABASE_URL=sqlite:///./studyflow.db
LLM_PROVIDER=mock
```

Para produção com Supabase PostgreSQL:

```env
DATABASE_URL=postgresql://postgres:SUA_SENHA@SEU_HOST:5432/postgres
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_KEY=sua_service_role_key
SUPABASE_STORAGE_BUCKET=studyflow-documents
```

## Deploy no Railway

O projeto já inclui:

```txt
Procfile
railway.json
nixpacks.toml
runtime.txt
```

Comando de start usado no Railway:

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## O que entrou na Build 3

- Frontend e backend unificados no FastAPI.
- Sistema inteiro rodando em uma única porta.
- Correção do botão `Sair`: agora limpa sessão local e volta para `/`.
- API movida para `/api`.
- Estrutura preparada para Railway.
- Configuração preparada para Supabase PostgreSQL.
- Upload preparado para Supabase Storage, com fallback local.
- Templates movidos para `backend/templates`.
- CSS/JS movidos para `backend/static`.
- Banco local ainda funciona com SQLite para testes rápidos.
- Usuário/notebook demo criados automaticamente para facilitar testes.

## Observação

A IA ainda está em modo `mock`. A próxima build deve ligar a IA real com Gemini, Groq ou OpenAI e melhorar o RAG com embeddings/pgvector.


## Build 4

Foco desta versão:

- Agente visual e comportamental.
- Seleção de múltiplos documentos na sidebar.
- Streaming de status do agente em `/api/chat/stream`.
- Logs detalhados no console do navegador e no terminal FastAPI.
- Detecção de múltiplas tarefas no mesmo comando.
- Preparação para ferramentas completas da Build 5.

Teste principal:

1. Rode `uvicorn app.main:app --reload` dentro de `backend`.
2. Acesse `http://127.0.0.1:8000`.
3. Envie PDF, DOCX ou TXT.
4. Marque uma ou mais fontes.
5. Envie um comando como: `Analise os documentos selecionados e prepare um resumo e um plano de estudo.`
6. Veja o streaming do agente e os logs no console.


## Build 4.1 - Correção de estabilidade

Esta versão corrige o travamento encontrado ao enviar PDFs grandes.

Correções aplicadas:

- Corrigido loop infinito no `chunk_text`, que podia repetir o último trecho do PDF e travar o PC.
- Listagem de documentos agora retorna apenas metadados: nome, tipo, tamanho, status, quantidade de caracteres e quantidade de chunks.
- Upload possui limite de segurança de 15 MB no frontend e no backend.
- Botão de upload fica bloqueado enquanto o arquivo está sendo processado, evitando envio duplicado.
- Recarregar a página com F5 não reprocessa PDF já enviado; a tela apenas recarrega os metadados salvos.
- Chat usa busca controlada de chunks e não tenta trabalhar com centenas de milhares de caracteres de uma vez.

Teste recomendado:

1. Rode o backend.
2. Acesse `http://127.0.0.1:8000`.
3. Envie um PDF menor que 15 MB.
4. Confira se a sidebar mostra `Processado`, tamanho e quantidade de chunks.
5. Aperte F5 e confira se o PDF não é reprocessado.
6. Selecione o documento e envie uma mensagem para o agente.
