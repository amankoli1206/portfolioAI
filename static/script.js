// PortfolioAI Client-Side Interactivity

// Modal helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
}

// Global dismiss for click outside modal content
window.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('active');
  }
});

// Confirmation helper
function confirmDelete(message) {
  return confirm(message || 'Are you sure you want to delete this portfolio record?');
}

// Tab navigation for pages that use client tabs
function switchTab(evt, tabName) {
  const tabContents = document.getElementsByClassName("tab-content");
  for (let i = 0; i < tabContents.length; i++) {
    tabContents[i].style.display = "none";
  }
  const tabBtns = document.getElementsByClassName("tab-btn");
  for (let i = 0; i < tabBtns.length; i++) {
    tabBtns[i].classList.remove("active");
  }
  const target = document.getElementById(tabName);
  if (target) target.style.display = "block";
  if (evt && evt.currentTarget) evt.currentTarget.classList.add("active");
}

// Copy to clipboard helper
function copyToClipboard(text, elemId) {
  navigator.clipboard.writeText(text).then(() => {
    const el = document.getElementById(elemId);
    if (el) {
      const orig = el.innerText;
      el.innerText = 'Copied!';
      setTimeout(() => { el.innerText = orig; }, 2000);
    }
  });
}
