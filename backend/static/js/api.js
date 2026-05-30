const API_BASE = '/api';
const state = {
  userId: Number(localStorage.getItem('studyflow_user_id') || 1),
  notebookId: Number(localStorage.getItem('studyflow_notebook_id') || 1),
  selectedDocumentIds: JSON.parse(localStorage.getItem('studyflow_selected_docs') || '[]'),
};

async function api(path, options = {}) {
  const headers = options.body instanceof FormData
    ? (options.headers || {})
    : { 'Content-Type': 'application/json', ...(options.headers || {}) };

  console.log('[API] Request:', `${API_BASE}${path}`, options);
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const raw = await res.text();
  if (!res.ok) {
    console.error('[API][ERRO]', res.status, raw);
    throw new Error(raw || `HTTP ${res.status}`);
  }
  try {
    const json = raw ? JSON.parse(raw) : {};
    console.log('[API] Response:', json);
    return json;
  } catch (err) {
    console.error('[API][JSON][ERRO]', err, raw);
    throw err;
  }
}

function setNotebookId(id) {
  state.notebookId = Number(id);
  state.selectedDocumentIds = [];
  localStorage.setItem('studyflow_notebook_id', String(id));
  localStorage.setItem('studyflow_selected_docs', '[]');
  updateSelectedCount?.();
}

function setSelectedDocumentIds(ids) {
  state.selectedDocumentIds = [...new Set(ids.map(Number).filter(Boolean))];
  localStorage.setItem('studyflow_selected_docs', JSON.stringify(state.selectedDocumentIds));
  updateSelectedCount?.();
}

function logout() {
  localStorage.removeItem('studyflow_token');
  localStorage.removeItem('studyflow_user_name');
  localStorage.removeItem('studyflow_user_email');
  window.location.href = '/';
}

document.addEventListener('DOMContentLoaded', () => {
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) logoutBtn.addEventListener('click', logout);
});
