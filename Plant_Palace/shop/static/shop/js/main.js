/**
 * Plant Palace — Main JavaScript
 * Handles: navbar scroll, back-to-top, cart AJAX, password toggle
 */

'use strict';

// ---- Navbar scroll effect ----
window.addEventListener('scroll', () => {
  const nav = document.getElementById('mainNav');
  if (nav) nav.classList.toggle('scrolled', window.scrollY > 60);
});

// ---- Back to top button ----
const backBtn = document.getElementById('backToTop');
if (backBtn) {
  window.addEventListener('scroll', () => {
    backBtn.style.display = window.scrollY > 300 ? 'flex' : 'none';
  });
  backBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

// ---- Password toggle helper ----
function togglePwd(inputId) {
  const el = document.getElementById(inputId);
  if (!el) return;
  el.type = el.type === 'password' ? 'text' : 'password';
}

// ---- Cart: Add to Cart via AJAX ----
document.querySelectorAll('.btn-add-cart').forEach(btn => {
  btn.addEventListener('click', async (e) => {
    e.preventDefault();
    const productId = btn.dataset.productId;
    const qty       = btn.dataset.qty || 1;
    const csrfToken = getCookie('csrftoken');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Adding…';

    try {
      const res = await fetch(`/cart/add/${productId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken':  csrfToken,
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: `quantity=${qty}`,
      });

      if (res.status === 302 || res.redirected) {
        // Not logged in — show login modal
        const modal = new bootstrap.Modal(document.getElementById('loginModal'));
        modal.show();
        btn.innerHTML = '<i class="bi bi-cart-plus me-1"></i>Add to Cart';
        btn.disabled = false;
        return;
      }

      const data = await res.json();
      if (data.status === 'ok') {
        // Update cart badge
        document.querySelectorAll('.cart-badge').forEach(b => {
          b.textContent = data.cart_count;
          b.classList.add('pulse');
          setTimeout(() => b.classList.remove('pulse'), 600);
        });
        showToast(data.message, 'success');
        btn.innerHTML = '<i class="bi bi-check2 me-1"></i>Added!';
        setTimeout(() => {
          btn.innerHTML = '<i class="bi bi-cart-plus me-1"></i>Add to Cart';
          btn.disabled = false;
        }, 1500);
      }
    } catch (err) {
      showToast('Something went wrong. Please try again.', 'danger');
      btn.innerHTML = '<i class="bi bi-cart-plus me-1"></i>Add to Cart';
      btn.disabled = false;
    }
  });
});

// ---- Toast notification ----
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer') || createToastContainer();
  const id = 'toast-' + Date.now();
  const icons = { success: 'bi-check-circle-fill', danger: 'bi-x-circle-fill', info: 'bi-info-circle-fill', warning: 'bi-exclamation-triangle-fill' };
  const icon  = icons[type] || 'bi-info-circle-fill';
  const html = `
    <div id="${id}" class="toast align-items-center text-bg-${type} border-0 mb-2" role="alert" aria-live="assertive">
      <div class="d-flex">
        <div class="toast-body"><i class="bi ${icon} me-2"></i>${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>`;
  container.insertAdjacentHTML('beforeend', html);
  const el   = document.getElementById(id);
  const toast = new bootstrap.Toast(el, { delay: 3500 });
  toast.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

function createToastContainer() {
  const div = document.createElement('div');
  div.id = 'toastContainer';
  div.style.cssText = 'position:fixed;top:80px;right:1rem;z-index:9999;min-width:260px;';
  document.body.appendChild(div);
  return div;
}

// ---- CSRF Cookie helper ----
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    document.cookie.split(';').forEach(cookie => {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
      }
    });
  }
  return cookieValue;
}

// ---- Cart quantity update (cart page) ----
document.querySelectorAll('.qty-decrease').forEach(btn => {
  btn.addEventListener('click', () => {
    const input = btn.closest('.qty-group').querySelector('.qty-value');
    const val   = parseInt(input.value);
    if (val > 1) input.value = val - 1;
  });
});
document.querySelectorAll('.qty-increase').forEach(btn => {
  btn.addEventListener('click', () => {
    const input = btn.closest('.qty-group').querySelector('.qty-value');
    const max   = parseInt(input.max || 99);
    const val   = parseInt(input.value);
    if (val < max) input.value = val + 1;
  });
});

// ---- Payment page: method toggle ----
document.querySelectorAll('.payment-method-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.payment-method-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const method = btn.dataset.method;
    const radio  = document.getElementById('pm_' + method);
    if (radio) radio.checked = true;
  });
});

// ---- Auto dismiss messages ----
document.querySelectorAll('.alert').forEach(el => {
  setTimeout(() => {
    const alert = bootstrap.Alert.getOrCreateInstance(el);
    if (alert) alert.close();
  }, 5000);
});

// ---- badge pulse animation ----
const style = document.createElement('style');
style.textContent = `.pulse { animation: pulseBadge .4s ease; } @keyframes pulseBadge { 0%,100%{transform:scale(1)} 50%{transform:scale(1.5)} }`;
document.head.appendChild(style);
