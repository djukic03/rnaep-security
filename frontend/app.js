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
      const stockBadge =
        p.quantity > 5
          ? `<span class="badge badge-green">Na stanju: ${p.quantity}</span>`
          : p.quantity > 0
            ? `<span class="badge badge-yellow">Malo na stanju: ${p.quantity}</span>`
            : `<span class="badge badge-red">Nema na stanju</span>`;

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

async function loadOrders() {
  const tbody = document.getElementById("orders-tbody");
  if (!tbody) return;

  try {
    const res = await fetch(`${GATEWAY_URL}/orders`);
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
      <td>${o.id}</td>
      <td>${o.product_id}</td>
      <td>${o.quantity}</td>
      <td>${o.note || "—"}</td>
      <td><span class="badge badge-green">Potvrđeno</span></td>
    </tr>
  `,
    )
    .join("");
}

function updateNavAuth() {
  const loggedIn = !!sessionStorage.getItem("access_token");
  const navOut = document.getElementById("nav-out");
  const navIn = document.getElementById("nav-in");
  if (!navOut || !navIn) return;

  navOut.style.display = loggedIn ? "none" : "flex";
  navIn.style.display = loggedIn ? "flex" : "none";
}

const ordersLocked = document.getElementById("orders-locked");
const ordersUnlocked = document.getElementById("orders-unlocked");

if (ordersLocked && ordersUnlocked) {
  const token = sessionStorage.getItem("access_token");
  if (!token) {
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
  const loggedIn = !!sessionStorage.getItem("access_token");
  orderAuthWarning.style.display = loggedIn ? "none" : "block";
  orderFormFields.style.display = loggedIn ? "block" : "none";
}

updateNavAuth();
loadProducts();