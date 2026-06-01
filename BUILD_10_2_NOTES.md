# Build 10.2 — Hotfix do agente em deploy

## Problema corrigido
Em ambiente de deploy, o upload funcionava, mas o chat podia terminar com erro no frontend:

```txt
A resposta terminou sem conteúdo.
```

Isso acontecia quando o stream SSE recebia apenas eventos de status e nenhum evento final de conteúdo.

## Correções

- Guardrail no backend para nunca retornar `answer` vazio.
- Fallback local seguro quando o LLM/agente retorna texto vazio.
- Fallback específico para quiz quando a normalização do bloco `quiz` fica vazia.
- Stream SSE agora mantém a conexão viva enquanto o agente/LLM trabalha.
- Heartbeats durante chamadas longas ao LLM em deploy.
- Timeout do frontend aumentado para 180s.
- Frontend não quebra a tela caso algum stream termine sem conteúdo final.
- Cache busting atualizado para `v=1.0.2`.

## Testes executados

- `python -m py_compile backend/app/*.py`
- `node --check backend/static/js/chat.js`
- `node --check backend/static/js/upload.js`
- `node --check backend/static/js/notebook.js`
- `node --check backend/static/js/api.js`
