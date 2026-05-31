# Testes do Agente - Build 5.2

## Correções principais

- Sanitização do nome do arquivo antes de enviar para Supabase Storage.
- Limpeza de IDs de documentos excluídos/obsoletos antes do envio do chat.
- Fallback controlado: se nenhum checkbox estiver marcado, o backend usa documentos processados recentes do notebook.
- Rota `/api/health/llm/test` para testar chamada real ao provider LLM.

## Testes recomendados

1. Enviar `Guia de Inteligência Artificial Aplicada para Profissões.pdf`.
   - Esperado: `storage_path` preenchido com nome sem acentos/espaços.

2. Excluir um documento e enviar mensagem no chat.
   - Esperado: frontend limpa IDs antigos; backend não recebe ID deletado como seleção válida.

3. Perguntar: `Faça um resumo, um questionário e um plano de estudo`.
   - Esperado: agente detecta `summary`, `quiz`, `study_plan` e usa documentos válidos.

4. Acessar `/api/health/llm/test`.
   - Esperado: `ok: true` se Groq/Gemini/OpenAI estiver funcionando.
