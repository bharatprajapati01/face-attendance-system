/* Toast system */
function showToast(message, type = 'info', duration = 4000) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${icons[type] || '📢'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => toast.classList.add('show'), 50);
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 400);
  }, duration);
}

/* Counter animation */
function animateCounter(el, target, duration = 1500, suffix = '') {
  const start = 0;
  const step = target / (duration / 16);
  let current = start;

  const update = () => {
    current = Math.min(current + step, target);
    el.textContent = Math.floor(current) + suffix;
    if (current < target) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

/* Initialize all counters on page */
function initCounters() {
  document.querySelectorAll('[data-counter]').forEach(el => {
    const target = parseFloat(el.dataset.counter);
    const suffix = el.dataset.suffix || '';
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(el, target, 1500, suffix);
          observer.disconnect();
        }
      });
    });
    observer.observe(el);
  });
}

/* Progress bar animation */
function initProgressBars() {
  document.querySelectorAll('.progress-fill').forEach(bar => {
    const target = bar.dataset.width || '0';
    bar.style.width = '0%';
    setTimeout(() => {
      bar.style.width = target + '%';
    }, 300);
  });
}

/* Flash messages auto-dismiss */
function initFlashMessages() {
  document.querySelectorAll('.flash-msg').forEach(msg => {
    setTimeout(() => {
      msg.style.opacity = '0';
      msg.style.transform = 'translateX(20px)';
      msg.style.transition = 'all 0.4s ease';
      setTimeout(() => msg.remove(), 400);
    }, 5000);
  });
}

/* Modal system */
function openModal(id) {
  const overlay = document.getElementById(id);
  if (overlay) {
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(id) {
  const overlay = document.getElementById(id);
  if (overlay) {
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }
}

/* Close modal on overlay click */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) closeModal(overlay.id);
    });
  });

  initCounters();
  initProgressBars();
  initFlashMessages();
});

/* Confirm delete */
function confirmDelete(form, name) {
  if (confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) {
    form.submit();
  }
}

/* Copy to clipboard */
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => showToast('Copied to clipboard!', 'success', 2000));
}

/* Format time */
function formatTime(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
}

/* Sidebar mobile toggle */
const menuToggle = document.getElementById('menuToggle');
const sidebar = document.querySelector('.sidebar');
if (menuToggle && sidebar) {
  menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
}
