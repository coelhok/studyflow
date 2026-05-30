const chatForm = document.getElementById('chatForm');
const input = document.getElementById('messageInput');
const chatBox = document.getElementById('chatBox');

if (chatForm) {
  chatForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    addMessage('user', text);
    await sendChatStream(text);
  });
}

document.querySelectorAll('.quick-actions button').forEach(btn => {
  btn.addEventListener('click', () => {
    input.value = btn.dataset.prompt;
    chatForm.requestSubmit();
  });
});

function addMessage(role, content) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = role === 'assistant'
    ? `<div class="avatar">✦</div><div class="bubble">${formatContent(content)}<small>agora</small></div>`
    : `<div class="bubble">${escapeHtml(content)}<small>agora</small></div>`;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  return div;
}

function getSelectedDocumentIds() {
  const checked = [...document.querySelectorAll('.doc-check:checked')].map(el => Number(el.value));
  if (checked.length) setSelectedDocumentIds(checked);
  return state.selectedDocumentIds || [];
}

async function sendChatStream(message) {
  const selectedIds = getSelectedDocumentIds();
  console.log('[CHAT] Mensagem digitada:', message);
  console.log('[CHAT] Documentos selecionados:', selectedIds);

  const placeholder = document.createElement('div');
  placeholder.className = 'msg assistant';
  placeholder.innerHTML = `
    <div class="avatar">✦</div>
    <div class="bubble">
      <div class="agent-progress">
        <strong>Agente trabalhando...</strong>
        <ul class="agent-steps" id="agentSteps-${Date.now()}"></ul>
      </div>
      <div class="stream-content"></div>
      <small>agora</small>
    </div>`;
  chatBox.appendChild(placeholder);
  const stepsList = placeholder.querySelector('.agent-steps');
  const contentBox = placeholder.querySelector('.stream-content');
  let finalText = '';

  updateAgentState('working', 'Agente trabalhando', 'Iniciando análise do pedido...', 'processando');

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60000);

  try {
    console.log('[CHAT] Chamando API stream...');
    const res = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: state.userId,
        notebook_id: state.notebookId,
        message,
        selected_document_ids: selectedIds,
      }),
      signal: controller.signal,
    });

    console.log('[CHAT] Status da resposta:', res.status);
    if (!res.ok || !res.body) {
      const errText = await res.text();
      console.error('[CHAT][ERRO] Resposta inválida:', res.status, errText);
      throw new Error(errText || `HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() || '';

      for (const evt of events) {
        const line = evt.split('\n').find(l => l.startsWith('data:'));
        if (!line) continue;
        const raw = line.replace(/^data:\s?/, '');
        try {
          const payload = JSON.parse(raw);
          console.log('[CHAT][STREAM]', payload);
          if (payload.type === 'status') {
            const li = document.createElement('li');
            li.textContent = payload.message;
            stepsList.appendChild(li);
            updateAgentState('working', 'Agente trabalhando', payload.message, 'streaming');
          }
          if (payload.type === 'content') {
            finalText += payload.message;
            contentBox.innerHTML = formatContent(finalText);
            chatBox.scrollTop = chatBox.scrollHeight;
          }
          if (payload.type === 'done') {
            updateAgentState('done', 'Agente finalizado', payload.message, 'concluído');
          }
        } catch (err) {
          console.error('[CHAT][STREAM][JSON][ERRO]', err, raw);
        }
      }
    }

    if (!finalText.trim()) {
      throw new Error('A resposta terminou sem conteúdo.');
    }
    renderMermaidBlocks();
  } catch (err) {
    console.error('[CHAT][ERRO] Erro ao enviar mensagem:', err);
    contentBox.innerHTML = '<p>Não consegui concluir a resposta. Verifique o console e o terminal do FastAPI.</p>';
    updateAgentState('error', 'Erro no agente', 'Não consegui concluir a resposta. Veja o console para detalhes.', 'erro');
  } finally {
    clearTimeout(timeout);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
}

function formatContent(text) {
  const escaped = escapeHtml(String(text || ''));
  return escaped
    .replace(/```mermaid([\s\S]*?)```/g, (_, code) => `<div class="mermaid-card"><pre class="mermaid">${code.trim()}</pre></div>`)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}

function escapeHtml(str) {
  return String(str).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

async function renderMermaidBlocks() {
  if (window.mermaid) {
    try { window.mermaid.initialize({ startOnLoad: false, theme: 'dark' }); await window.mermaid.run(); } catch(e) { console.warn(e); }
  }
}
