# StudyFlow PDF AI - Build 6.1

Correções desta build:

- Upload autenticado enviando `Authorization: Bearer <token>`.
- Upload com suporte real a múltiplos arquivos no mesmo envio.
- Backend processa vários PDF/DOCX/TXT em sequência.
- Cada arquivo gera seu próprio registro em `documents` e chunks em `document_chunks`.
- Cada arquivo usa o `user_id` do token e o notebook ativo, não `user_id=1`.
- Se um arquivo falhar, os demais continuam sendo processados.
- Retorno do upload inclui `uploaded`, `errors`, `count` e `error_count`.
- O input de arquivo agora usa `multiple`.
- Mantido isolamento por usuário criado na Build 6.

## Teste recomendado

1. Criar usuário A.
2. Enviar 2 ou 3 PDFs juntos.
3. Confirmar que todos aparecem no notebook.
4. Sair.
5. Criar usuário B.
6. Confirmar que usuário B não vê arquivos do usuário A.
7. Enviar arquivos no usuário B.
8. Voltar para usuário A e confirmar que os arquivos dele continuam separados.

## Rotas envolvidas

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/documents/upload`
- `GET /api/documents`
- `DELETE /api/documents/{id}`
- `POST /api/chat/stream`
