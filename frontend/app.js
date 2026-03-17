const GATEWAY_URL = "http://localhost:8000";

async function loadProducts() {
  const list = document.getElementById("product-list");
  if (!list) return;

  try {
    const res = await fetch(`${GATEWAY_URL}/products`);
    const products = await res.json();
    renderProducts(products);
    populateOrderSelect(products);
  } catch (err) {
    list.innerHTML =
      '<div class="loading">Greška pri učitavanju proizvoda.</div>';
  }
}

function renderProducts(products) {
  const list = document.getElementById("product-list");
  if (!list) return;

  if (!products.length) {
    list.innerHTML = '<div class="loading">Nema proizvoda.</div>';
    return;
  }

  list.innerHTML = products
    .map((p) => {
      const stockBadge = `<span class="badge badge-green">Na stanju: ${p.quantity}</span>`;

      return `
      <div class="product-row">
        <div>
          <div class="product-name">${p.name}</div>
          <div class="product-info">product_id: ${p.id} &nbsp;·&nbsp; ${stockBadge}</div>
        </div>
        <div style="display:flex; align-items:center; gap:12px;">
          <span class="product-price">$${p.price.toLocaleString()}</span>
        </div>
      </div>
    `;
    })
    .join("");
}

function populateOrderSelect(products) {
  const select = document.getElementById("order-product");
  if (!select) return;
  select.innerHTML = products
    .map(
      (p) =>
        `<option value="${p.id}">${p.name} — $${p.price.toLocaleString()}</option>`,
    )
    .join("");
}

document.getElementById("btn-order")?.addEventListener("click", async () => {
  const product_id = document.getElementById("order-product").value;
  const quantity = parseInt(document.getElementById("order-qty").value);
  const note = document.getElementById("order-note").value.trim();

  const res = await fetch(`${GATEWAY_URL}/orders`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    credentials: "include",
    body: JSON.stringify({ product_id, quantity, note }),
  });

  if (res.ok) {
    alert("Porudžbina uspešno kreirana!");
    document.getElementById("order-product").selectedIndex = 0;
    document.getElementById("order-qty").value = "1";
    document.getElementById("order-note").value = "";
  } else {
    const data = await res.json();
    alert(data.detail || "Greška pri kreiranju porudžbine.");
  }
});

async function loadOrders() {
  const tbody = document.getElementById("orders-tbody");
  if (!tbody) return;

  try {
    const res = await fetch(`${GATEWAY_URL}/orders`, {
      credentials: "include"
    });
    const orders = await res.json();
    renderOrders(orders);
  } catch (err) {
    tbody.innerHTML =
      '<tr><td colspan="5" class="empty">Greška pri učitavanju porudžbina.</td></tr>';
  }
}

function renderOrders(orders) {
  const tbody = document.getElementById("orders-tbody");
  if (!tbody) return;

  if (!orders.length) {
    tbody.innerHTML =
      '<tr><td colspan="5" class="empty">Nema porudžbina.</td></tr>';
    return;
  }

  tbody.innerHTML = orders
    .map(
      (o) => `
    <tr>
      <td>${o.product_id}</td>
      <td>${o.quantity}</td>
      <td>${o.note || "—"}</td>
    </tr>
  `,
    )
    .join("");
}


async function loadUsers() {
  const tbody = document.getElementById("users-tbody");
  if (!tbody) return;

  try {
    const res = await fetch(`${GATEWAY_URL}/users`, {
      credentials: "include"
    });
    const users = await res.json();
    tbody.innerHTML = users.map(u => `
      <tr>
        <td>${u.id}</td>
        <td>${u.username}</td>
        <td><span class="badge ${u.role === 'admin' ? 'badge-red' : 'badge-blue'}">${u.role}</span></td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML =
      '<tr><td colspan="3" class="empty">Greška pri učitavanju korisnika.</td></tr>';
  }
}

const usersForbidden = document.getElementById("users-forbidden");
const usersLocked    = document.getElementById('users-locked');
const usersUnlocked  = document.getElementById('users-unlocked');

if (usersForbidden && usersLocked && usersUnlocked) {
  const role   = sessionStorage.getItem('role');

  if (!role) {
    usersLocked.style.display    = 'block';
    usersForbidden.style.display = 'none';
    usersUnlocked.style.display  = 'none';
  } else if (role !== 'admin') {
    usersForbidden.style.display = 'block';
    usersLocked.style.display    = 'none';
    usersUnlocked.style.display  = 'none';
  } else {
    usersUnlocked.style.display  = 'block';
    usersForbidden.style.display = 'none';
    usersLocked.style.display    = 'none';
    loadUsers();
  }
}






function updateNavAuth() {
  const loggedIn = !!sessionStorage.getItem("role");
  const navOut = document.getElementById("nav-out");
  const navIn = document.getElementById("nav-in");
  if (!navOut || !navIn) return;

  navOut.style.display = loggedIn ? "none" : "flex";
  navIn.style.display = loggedIn ? "flex" : "none";
}

const ordersLocked = document.getElementById("orders-locked");
const ordersUnlocked = document.getElementById("orders-unlocked");

if (ordersLocked && ordersUnlocked) {
  const role = sessionStorage.getItem("role");
  if (!role) {
    ordersLocked.style.display = "block";
    ordersUnlocked.style.display = "none";
  } else {
    ordersLocked.style.display = "none";
    ordersUnlocked.style.display = "block";
    loadOrders();
  }
}

const orderAuthWarning = document.getElementById("order-auth-warning");
const orderFormFields = document.getElementById("order-form-fields");

if (orderAuthWarning && orderFormFields) {
  const loggedIn = !!sessionStorage.getItem("role");
  orderAuthWarning.style.display = loggedIn ? "none" : "block";
  orderFormFields.style.display = loggedIn ? "block" : "none";
}

updateNavAuth();
loadProducts();