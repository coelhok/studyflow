const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');

function saveSession(payload) {
  localStorage.setItem('studyflow_token', payload.token || 'dev-token');
  localStorage.setItem('studyflow_user_id', String(payload.user?.id || 1));
  localStorage.setItem('studyflow_user_name', payload.user?.name || 'Usuário');
  localStorage.setItem('studyflow_user_email', payload.user?.email || 'usuario@local');
  if (payload.default_notebook_id) localStorage.setItem('studyflow_notebook_id', String(payload.default_notebook_id));
  window.location.href = '/dashboard';
}

if (loginForm) {
  loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const payload = await api('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          email: document.getElementById('email').value,
          password: document.getElementById('password').value,
        })
      });
      saveSession(payload);
    } catch {
      alert('Login inválido. Crie uma conta ou use um usuário cadastrado.');
    }
  });
}

if (registerForm) {
  registerForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const payload = await api('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          name: document.getElementById('name').value,
          email: document.getElementById('email').value,
          password: document.getElementById('password').value,
        })
      });
      saveSession(payload);
    } catch (err) {
      alert('Não foi possível cadastrar. Talvez esse e-mail já exista ou a senha seja curta.');
    }
  });
}
