const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const MAX_UPLOAD_MB = 15;
const MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024;

if (fileInput) {
  fileInput.addEventListener('change', () => {
    const file = fileInput.files?.[0];
    console.log('[UPLOAD] Arquivo selecionado:', file);
    fileName.textContent = file?.name || 'Escolher PDF, DOCX ou TXT';
  });
}

if (uploadForm) {
  uploadForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!fileInput.files.length) return showToast('Selecione um PDF, DOCX ou TXT.', 'warn');

    const file = fileInput.files[0];
    console.log('[UPLOAD] Iniciando upload:', { name: file.name, size: file.size, type: file.type });
    if (file.size > MAX_UPLOAD_BYTES) {
      console.warn('[UPLOAD] Arquivo recusado no frontend por tamanho:', file.size);
      setStatus('uploadStatus', `Arquivo muito grande. Limite: ${MAX_UPLOAD_MB} MB`, false);
      updateAgentState('error', 'Arquivo muito grande', `Esse arquivo passa de ${MAX_UPLOAD_MB} MB.`, 'erro');
      return showToast(`Arquivo muito grande. Limite: ${MAX_UPLOAD_MB} MB.`, 'warn');
    }
    const form = new FormData();
    form.append('file', file);
    form.append('user_id', state.userId);
    form.append('notebook_id', state.notebookId);

    const submitBtn = uploadForm.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;
    setStatus('uploadStatus', 'Processando arquivo...', false);
    updateAgentState('working', 'Agente acompanhando upload', `Processando ${file.name}...`, 'upload');

    try {
      const res = await fetch(`${API_BASE}/documents/upload`, { method: 'POST', body: form });
      const raw = await res.text();
      console.log('[UPLOAD] Resposta bruta:', res.status, raw);
      if (!res.ok) {
        console.error('[UPLOAD][ERRO]', res.status, raw);
        setStatus('uploadStatus', 'Erro ao salvar arquivo', false);
        updateAgentState('error', 'Erro no upload', 'Não consegui processar esse arquivo. Veja o console para detalhes.', 'erro');
        return showToast('Erro ao enviar arquivo.', 'warn');
      }
      const data = raw ? JSON.parse(raw) : {};
      console.log('[UPLOAD] Upload concluído:', data);
      fileInput.value = '';
      fileName.textContent = 'Escolher PDF, DOCX ou TXT';
      setStatus('uploadStatus', `Arquivo salvo: ${data.chunks || 0} chunks`, true);
      await loadDocuments();
      updateAgentState('idle', 'Fonte pronta', `${data.filename} foi processado e já pode ser selecionado.`, 'pronto');
      showToast('Arquivo salvo e processado.');
    } catch (err) {
      console.error('[UPLOAD][ERRO] Falha inesperada:', err);
      setStatus('uploadStatus', 'Erro ao salvar arquivo', false);
      updateAgentState('error', 'Erro no upload', 'Falha inesperada no envio do arquivo.', 'erro');
      showToast('Erro ao enviar arquivo.', 'warn');
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  });
}

async function loadDocuments() {
  const list = document.getElementById('documentList');
  if (!list) return;
  try {
    console.log('[UPLOAD] Carregando documentos...', { userId: state.userId, notebookId: state.notebookId });
    const docs = await api(`/documents?user_id=${state.userId}&notebook_id=${state.notebookId}`);
    const existingIds = docs.map(d => Number(d.id));
    const validSelected = state.selectedDocumentIds.filter(id => existingIds.includes(Number(id)));
    if (validSelected.length !== state.selectedDocumentIds.length) setSelectedDocumentIds(validSelected);

    list.innerHTML = docs.map(d => {
      const id = Number(d.id);
      const checked = state.selectedDocumentIds.includes(id) || (state.selectedDocumentIds.length === 0 && docs.length === 1);
      if (checked && !state.selectedDocumentIds.includes(id)) {
        state.selectedDocumentIds.push(id);
        localStorage.setItem('studyflow_selected_docs', JSON.stringify(state.selectedDocumentIds));
      }
      const statusClass = d.status === 'processed' ? 'ok' : (d.status === 'error' ? 'bad' : 'warn');
      const statusText = d.status === 'processed' ? 'Processado' : (d.status === 'empty' ? 'Sem texto extraído' : d.status);
      const sizeMb = d.file_size ? `${(Number(d.file_size) / 1024 / 1024).toFixed(2)} MB` : 'tamanho n/d';
      const chunkInfo = d.chunk_count ? `${d.chunk_count} chunks` : '0 chunks';
      return `
        <label class="doc-item selectable ${checked ? 'selected' : ''}" data-doc-id="${id}">
          <input class="doc-check" type="checkbox" value="${id}" ${checked ? 'checked' : ''} />
          <div class="item-icon ${escapeHtml(d.file_type)}">${escapeHtml(d.file_type).toUpperCase()}</div>
          <div class="item-text"><strong>${escapeHtml(d.filename)}</strong><div class="meta"><span class="dot ${statusClass}"></span>${escapeHtml(statusText)} · ${escapeHtml(sizeMb)} · ${escapeHtml(chunkInfo)} · fonte ${checked ? 'selecionada' : 'disponível'}</div></div>
        </label>
      `;
    }).join('') || '<div class="meta">Nenhum arquivo enviado ainda.</div>';

    list.querySelectorAll('.doc-check').forEach(check => {
      check.addEventListener('change', () => {
        const ids = [...list.querySelectorAll('.doc-check:checked')].map(el => Number(el.value));
        console.log('[UPLOAD] Documentos selecionados:', ids);
        setSelectedDocumentIds(ids);
        loadDocuments();
      });
    });

    updateSelectedCount();
    setStatus('uploadStatus', docs.length ? `${state.selectedDocumentIds.length} fonte(s) selecionada(s)` : 'Nenhum arquivo enviado', Boolean(docs.length));
  } catch (err) {
    console.error('[UPLOAD][ERRO] Não foi possível carregar documentos:', err);
    list.innerHTML = '<div class="meta">Não foi possível carregar documentos.</div>';
  }
}
