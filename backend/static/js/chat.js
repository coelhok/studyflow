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

document.addEventListener('click', async (event) => {
  const copyBtn = event.target.closest('[data-copy-target]');
  if (!copyBtn) return;
  const selector = copyBtn.dataset.copyTarget;
  const target = selector ? document.querySelector(selector) : null;
  const text = target?.dataset.raw || target?.innerText || '';
  if (!text.trim()) return;
  try {
    await navigator.clipboard.writeText(text);
    copyBtn.textContent = 'Copiado';
    setTimeout(() => (copyBtn.textContent = copyBtn.dataset.label || 'Copiar'), 1500);
  } catch (err) {
    console.error('[CHAT][COPY][ERRO]', err);
  }
});

function addMessage(role, content) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = role === 'assistant'
    ? `<div class="avatar">✦</div><div class="bubble">${formatContent(content)}<small>agora</small></div>`
    : `<div class="bubble">${escapeHtml(content)}<small>agora</small></div>`;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  setTimeout(renderMermaidBlocks, 0);
  return div;
}

function getSelectedDocumentIds() {
  const availableIds = [...document.querySelectorAll('.doc-check')].map(el => String(el.value));
  const checked = [...document.querySelectorAll('.doc-check:checked')].map(el => String(el.value));
  const validChecked = checked.filter(id => availableIds.includes(id));
  const staleState = (state.selectedDocumentIds || []).filter(id => !availableIds.includes(String(id)));
  if (staleState.length) {
    console.warn('[CHAT] IDs de documentos removidos/obsoletos foram limpos:', staleState);
  }
  setSelectedDocumentIds(validChecked);
  updateSelectedCount?.();
  return validChecked;
}

async function sendChatStream(message) {
  const selectedIds = getSelectedDocumentIds();
  console.log('[CHAT] Mensagem digitada:', message);
  console.log('[CHAT] Documentos selecionados após limpeza:', selectedIds);
  if (!selectedIds.length) console.log('[CHAT] Nenhum checkbox marcado; backend pode usar fallback controlado do último documento processado.');

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
  const timeout = setTimeout(() => controller.abort(), 90000);

  try {
    console.log('[CHAT] Chamando API stream...');
    const res = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
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
            contentBox.innerHTML = formatContent(finalText, { streaming: true });
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
    contentBox.innerHTML = formatContent(finalText, { streaming: false });
    await renderMermaidBlocks();
  } catch (err) {
    console.error('[CHAT][ERRO] Erro ao enviar mensagem:', err);
    contentBox.innerHTML = '<p>Não consegui concluir a resposta. Verifique o console e o terminal do FastAPI.</p>';
    updateAgentState('error', 'Erro no agente', 'Não consegui concluir a resposta. Veja o console para detalhes.', 'erro');
  } finally {
    clearTimeout(timeout);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
}

function normalizeMermaidFences(text) {
  const lines = String(text || '').split('\n');
  const out = [];
  let i = 0;
  let insideFence = false;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();
    if (trimmed.startsWith('```')) {
      insideFence = !insideFence;
      out.push(line);
      i += 1;
      continue;
    }
    if (!insideFence && /^(graph|flowchart)\s+(TD|LR|BT|RL)/i.test(trimmed)) {
      const block = [trimmed];
      i += 1;
      while (i < lines.length) {
        const current = lines[i];
        const t = current.trim();
        if (!t || t.startsWith('## ') || /^(Explicação|Conclusão|Fontes usadas|Este fluxograma|Esse fluxograma)/i.test(t)) break;
        if (/^[-*]\s/.test(t) && !/[\[\]{}()<>-]/.test(t)) break;
        block.push(current);
        i += 1;
      }
      out.push('```mermaid');
      out.push(block.join('\n'));
      out.push('```');
      continue;
    }
    out.push(line);
    i += 1;
  }
  return out.join('\n');
}

function stripEmptyFlowchartHeadingBeforeMermaid(text) {
  // Build 5.4: evita card duplicado de Fluxograma quando o LLM retorna
  // "## Fluxograma" imediatamente antes do bloco Mermaid.
  return String(text || '')
    .replace(/(^|\n)##\s*(Fluxograma|Diagrama)\s*\n+(?=```mermaid)/gi, '\n')
    .replace(/(^|\n)##\s*(Fluxograma|Diagrama)\s*\n+$/gi, '\n');
}

function formatContent(text, options = {}) {
  const normalized = stripEmptyFlowchartHeadingBeforeMermaid(normalizeMermaidFences(text));
  const tokens = [];
  const regex = /```mermaid\s*([\s\S]*?)```/gi;
  let lastIndex = 0;
  let match;
  while ((match = regex.exec(normalized)) !== null) {
    if (match.index > lastIndex) tokens.push({ type: 'text', value: normalized.slice(lastIndex, match.index) });
    tokens.push({ type: 'mermaid', value: match[1].trim() });
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < normalized.length) tokens.push({ type: 'text', value: normalized.slice(lastIndex) });

  return tokens.map(token => {
    if (token.type === 'mermaid') return renderMermaidCard(token.value);
    return renderTextCards(token.value, options);
  }).join('');
}

function renderTextCards(text, options = {}) {
  const clean = String(text || '').trim();
  if (!clean) return '';

  const parts = splitMarkdownSections(clean);
  if (parts.length <= 1 && !/^##\s+/m.test(clean)) {
    return `<div class="answer-text">${inlineMarkdown(escapeHtml(clean)).replace(/\n/g, '<br>')}</div>`;
  }

  const usableParts = parts.filter(section => {
    const type = classifySection(section.title);
    const body = String(section.body || '').trim();
    // Build 5.4: não cria card vazio de Fluxograma se o Mermaid já virou card visual.
    return !(type === 'flowchart' && !body);
  });
  if (!usableParts.length) return '';
  return `<div class="material-grid">${usableParts.map(section => {
    const type = classifySection(section.title);
    const title = section.title || 'Resposta';
    const body = inlineMarkdown(escapeHtml(section.body || '')).replace(/\n/g, '<br>');
    return `
      <section class="material-card ${type}">
        <div class="material-head">
          <span class="material-icon">${iconFor(type)}</span>
          <strong>${escapeHtml(title)}</strong>
        </div>
        <div class="material-body">${body}</div>
      </section>`;
  }).join('')}</div>`;
}

function splitMarkdownSections(text) {
  const lines = String(text || '').split('\n');
  const sections = [];
  let current = { title: '', body: [] };
  for (const line of lines) {
    const m = line.match(/^##\s+(.+)\s*$/);
    if (m) {
      if (current.title || current.body.join('\n').trim()) sections.push({ title: current.title, body: current.body.join('\n').trim() });
      current = { title: m[1].trim(), body: [] };
    } else {
      current.body.push(line);
    }
  }
  if (current.title || current.body.join('\n').trim()) sections.push({ title: current.title, body: current.body.join('\n').trim() });
  return sections;
}

function classifySection(title) {
  const t = normalizeString(title);
  if (t.includes('resumo')) return 'summary';
  if (t.includes('questionario') || t.includes('quiz')) return 'quiz';
  if (t.includes('plano')) return 'study-plan';
  if (t.includes('fluxograma') || t.includes('diagrama')) return 'flowchart';
  if (t.includes('flashcard')) return 'flashcards';
  if (t.includes('revisao')) return 'review';
  if (t.includes('fonte')) return 'sources';
  return 'generic';
}

function iconFor(type) {
  return ({
    summary: '▣', quiz: '▦', 'study-plan': '▥', flowchart: '▤', flashcards: '▧', review: '⚡', sources: '⌁', generic: '✦'
  })[type] || '✦';
}

function renderMermaidCard(code) {
  const id = `mermaid-${Math.random().toString(16).slice(2)}`;
  const raw = String(code || '').trim();
  return `
    <section class="material-card flowchart mermaid-wrap">
      <div class="material-head">
        <span class="material-icon">▤</span>
        <strong>Fluxograma</strong>
        <button class="copy-btn" data-label="Copiar" data-copy-target="#${id}-code" type="button">Copiar</button>
      </div>
      <div class="mermaid-stage">
        <pre id="${id}" class="mermaid" data-raw="${escapeHtml(raw)}">${escapeHtml(raw)}</pre>
      </div>
      <pre id="${id}-code" class="mermaid-code" data-raw="${escapeHtml(raw)}">${escapeHtml(raw)}</pre>
    </section>`;
}

function inlineMarkdown(html) {
  return html
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^\s*[-*]\s+(.+)$/gm, '• $1');
}

function normalizeString(str) {
  return String(str || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

function escapeHtml(str) {
  return String(str).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

async function renderMermaidBlocks() {
  if (!window.mermaid) {
    console.warn('[MERMAID] Biblioteca não carregada.');
    return;
  }
  try {
    window.mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'strict' });
    await window.mermaid.run({ querySelector: '.mermaid' });
  } catch (e) {
    console.warn('[MERMAID][ERRO]', e);
  }
}
