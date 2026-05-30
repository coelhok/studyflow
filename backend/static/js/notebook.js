document.addEventListener('DOMContentLoaded', async () => {
  console.log('[NOTEBOOK] Inicializando notebook', state);
  await loadNotebooks();
  await loadDocuments();
  updateAgentState('idle', 'Agente pronto', 'Selecione uma ou mais fontes e envie um comando.', 'aguardando');
});

function showToast(message, type = 'ok') {
  const old = document.querySelector('.toast');
  if (old) old.remove();
  const div = document.createElement('div');
  div.className = 'toast';
  if (type === 'warn') div.style.background = '#231b09', div.style.color = '#facc15', div.style.borderColor = '#6b5413';
  div.textContent = message;
  document.body.appendChild(div);
  setTimeout(() => div.remove(), 3200);
}

function setStatus(id, text, ok = true) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.classList.toggle('warn', !ok);
}

function updateSelectedCount() {
  const el = document.getElementById('selectedCount');
  if (!el) return;
  const count = state.selectedDocumentIds.length;
  el.textContent = `${count} selecionada${count === 1 ? '' : 's'}`;
}

function updateAgentState(kind, title, text, pill) {
  const box = document.getElementById('agentState');
  const stateText = document.getElementById('agentStateText');
  const pillEl = document.getElementById('agentModePill');
  if (!box || !stateText || !pillEl) return;
  box.className = `agent-state ${kind || 'idle'}`;
  box.querySelector('strong').textContent = title || 'Agente pronto';
  stateText.textContent = text || '';
  pillEl.textContent = pill || 'aguardando';
}

async function loadNotebooks() {
  const list = document.getElementById('notebookList');
  if (!list) return;
  try {
    console.log('[NOTEBOOK] Carregando notebooks...');
    const notebooks = await api(`/notebooks?user_id=${state.userId}`);
    if (notebooks[0] && !state.notebookId) setNotebookId(notebooks[0].id);
    list.innerHTML = notebooks.map((n, i) => `
      <button class="session-item ${Number(state.notebookId) === Number(n.id) || (!state.notebookId && i === 0) ? 'active' : ''}" data-id="${n.id}" type="button">
        <div class="item-icon">▤</div>
        <div class="item-text"><strong>${escapeHtml(n.title)}</strong><div class="meta">Hoje · ${new Date().toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit'})}</div></div>
      </button>
    `).join('') || '<div class="empty">Nenhuma sessão criada.</div>';

    list.querySelectorAll('[data-id]').forEach(btn => {
      btn.addEventListener('click', async () => {
        console.log('[NOTEBOOK] Selecionando notebook:', btn.dataset.id);
        setNotebookId(btn.dataset.id);
        await loadNotebooks();
        await loadDocuments();
      });
    });
    setStatus('dbStatus', 'Sessão restaurada do banco', true);
  } catch (err) {
    console.error('[NOTEBOOK][ERRO] Falha ao carregar notebooks:', err);
    list.innerHTML = '<div class="meta">Backend offline. Rode o FastAPI.</div>';
    setStatus('dbStatus', 'Backend offline', false);
  }
}

const newNotebookBtn = document.getElementById('newNotebookBtn');
if (newNotebookBtn) {
  newNotebookBtn.addEventListener('click', async () => {
    try {
      console.log('[NOTEBOOK] Criando novo notebook...');
      const nb = await api('/notebooks', { method: 'POST', body: JSON.stringify({ user_id: state.userId, title: 'Novo notebook' }) });
      setNotebookId(nb.id);
      await loadNotebooks();
      await loadDocuments();
      showToast('Novo notebook criado.');
    } catch (err) {
      console.error('[NOTEBOOK][ERRO] Não foi possível criar notebook:', err);
      showToast('Não foi possível criar notebook.', 'warn');
    }
  });
}
