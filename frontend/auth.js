document.getElementById("btn-login")?.addEventListener("click", async () => {
    const redirectUri = 'http://localhost:3000/login.html';
    const clientId = 'frontend';
    window.location.href = `${GATEWAY_URL}/authorize?client_id=${clientId}&redirect_uri=${redirectUri}`;
});

document.getElementById("btn-register")?.addEventListener("click", async () => {
  const username = document.getElementById('reg-username').value.trim();
  const password = document.getElementById('reg-password').value.trim();

  if (!username || !password) {
    alert('Popunite sva polja.');
    return;
  }

  const res = await fetch(`${GATEWAY_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  if (res.ok) {
    alert('Uspešna registracija!');
    window.location.href = 'login.html';
  } else {
    const data = await res.json();
    alert(data.detail || 'Greška pri registraciji.');
  }
});

document.getElementById("btn-logout")?.addEventListener("click", () => {
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('role');
  alert('Uspešno odjavljeni!');
  window.location.href = 'shop.html';
});

async function handleCallback() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  if (!code) return;

  const res = await fetch(`${GATEWAY_URL}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ auth_code: code })
  });

  if (res.ok) {
    const data = await res.json();
    sessionStorage.setItem('access_token', data.access_token);
    sessionStorage.setItem('role', data.role);
    alert('Uspešna prijava!');
    window.location.href = 'shop.html';
  } else {
    alert('Greška pri razmeni tokena.');
  }
}

handleCallback();