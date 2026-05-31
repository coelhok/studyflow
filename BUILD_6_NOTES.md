# StudyFlow PDF AI — Build 6

## Foco da build

Autenticação real, sessão persistente e isolamento de dados por usuário.

## O que mudou

- Cadastro real em `/api/auth/register`.
- Login real em `/api/auth/login`.
- Sessão persistente com token assinado no navegador.
- Rota `/api/auth/me` para restaurar usuário após F5.
- Rotas de notebooks, documentos e chat agora usam o usuário autenticado pelo token.
- Removido uso de `user_id=1` no frontend.
- Cada usuário vê somente:
  - seus notebooks;
  - seus PDFs;
  - seus chunks;
  - seu histórico;
  - seus materiais gerados.
- Upload usa o `user_id` da sessão, não do frontend.
- Chat usa apenas documentos do usuário logado.
- Delete de documento respeita usuário autenticado.

## Testes recomendados

1. Criar usuário A.
2. Enviar um PDF com usuário A.
3. Sair.
4. Criar usuário B.
5. Conferir que o usuário B não vê os PDFs do usuário A.
6. Enviar PDF com usuário B.
7. Sair e voltar com usuário A.
8. Confirmar que o PDF do usuário A continua salvo.
9. Testar F5 no dashboard/notebook e confirmar que a sessão continua.
10. Testar chat com PDF do usuário A e depois com PDF do usuário B.

## Observação de segurança

A Build 6 usa token assinado por HMAC via `JWT_SECRET`. Configure uma chave forte no `.env` antes do deploy:

```env
JWT_SECRET=sua_chave_forte_aqui
```

Para produção, mantenha o `.env` fora do GitHub.
