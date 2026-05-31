# Build 5.4 - Correções de lapidação do agente

## Correções feitas

- Corrigido card duplicado de **Fluxograma** quando a resposta vinha com `## Fluxograma` antes do bloco Mermaid.
- Frontend agora remove título vazio de fluxograma quando já existe um card Mermaid visual.
- Prompt do agente refinado para fluxograma:
  - gera um único bloco Mermaid;
  - evita introdução e conclusão desnecessárias;
  - pede 5 a 8 nós curtos baseados no conteúdo central do documento;
  - deixa explicação curta separada.
- Botão **Excluir** agora evita clique duplo e deleção duplicada.
- DELETE de documento ficou idempotente no backend: se o documento já foi removido, retorna OK em vez de quebrar com 404.
- Melhor indicação visual de fonte ativa quando há apenas um documento no notebook e nenhum checkbox está marcado.
- Documento único sem checkbox marcado aparece como **fonte ativa** para deixar claro o fallback do agente.

## Testes recomendados

1. Subir backend e abrir `/notebook`.
2. Enviar um PDF com nome grande e acentos.
3. Conferir se o Storage salva com nome sanitizado.
4. Clicar em excluir várias vezes rapidamente e confirmar que não gera 404 problemático.
5. Enviar um PDF único, não marcar checkbox e pedir:
   - `Crie um fluxograma.`
6. Conferir se aparece só um card de fluxograma e se o Mermaid renderiza.
7. Pedir:
   - `Faça um resumo, um questionário e um plano de estudo.`
8. Conferir se as seções aparecem em cards separados e com fontes usadas.

## Observação

A Build 5.4 não muda banco, Storage ou Groq. Ela foca em comportamento visual, fluxo de exclusão e qualidade do fluxograma.
