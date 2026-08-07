/* Campus Placement & Interview Management System - Core Client JS */

// Toast Notification Manager
function showToast(message, type = 'info') {
  let toastContainer = document.querySelector('.toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  toast.className = `toast-alert ${type}`;
  
  let icon = 'fa-info-circle';
  if (type === 'success') icon = 'fa-check-circle';
  if (type === 'error') icon = 'fa-exclamation-circle';
  if (type === 'warning') icon = 'fa-triangle-exclamation';

  toast.innerHTML = `
    <i class="fas ${icon}" style="font-size: 1.2rem; color: var(--${type === 'info' ? 'primary' : type})"></i>
    <div style="flex: 1; font-weight: 600; font-size: 0.9rem;">${message}</div>
    <i class="fas fa-times" style="cursor: pointer; opacity: 0.6;" onclick="this.parentElement.remove()"></i>
  `;

  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Password Visibility Toggle
function togglePasswordVisibility(inputId, iconEl) {
  const input = document.getElementById(inputId);
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    iconEl.classList.replace('fa-eye', 'fa-eye-slash');
  } else {
    input.type = 'password';
    iconEl.classList.replace('fa-eye-slash', 'fa-eye');
  }
}

// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', () => {
  const mobileBtn = document.querySelector('.mobile-toggle');
  const navMenu = document.querySelector('.nav-menu');

  if (mobileBtn && navMenu) {
    mobileBtn.addEventListener('click', () => {
      navMenu.classList.toggle('active');
      const icon = mobileBtn.querySelector('i');
      if (icon) {
        icon.classList.toggle('fa-bars');
        icon.classList.toggle('fa-times');
      }
    });
  }

  // Password Validation Meter (for registration)
  const regPassword = document.getElementById('reg_password');
  if (regPassword) {
    regPassword.addEventListener('input', function() {
      const val = this.value;
      const lenCheck = document.getElementById('length-validation');
      const numCheck = document.getElementById('number-validation');
      const letCheck = document.getElementById('letter-validation');

      if (lenCheck) lenCheck.style.color = val.length >= 8 ? '#10b981' : '#64748b';
      if (numCheck) numCheck.style.color = /\d/.test(val) ? '#10b981' : '#64748b';
      if (letCheck) letCheck.style.color = /[a-zA-Z]/.test(val) ? '#10b981' : '#64748b';
    });
  }

  // File Dropzone Preview Handler
  const dropzones = document.querySelectorAll('.file-dropzone');
  dropzones.forEach(zone => {
    const input = zone.querySelector('input[type="file"]');
    const preview = zone.querySelector('.file-preview');

    if (input && preview) {
      input.addEventListener('change', () => {
        if (input.files.length > 0) {
          preview.innerHTML = `<i class="fas fa-file-check"></i> ${input.files[0].name}`;
          zone.style.borderColor = 'var(--success)';
        }
      });
    }
  });
});

// Registration Form Handler
document.getElementById('registrationForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  
  const submitBtn = this.querySelector('button[type="submit"]');
  const originalBtnText = submitBtn ? submitBtn.innerHTML : 'Register';
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';
  }

  const username = document.getElementById('reg_username').value.trim();
  const first_name = document.getElementById('reg_first_name').value.trim();
  const last_name = document.getElementById('reg_last_name').value.trim();
  const mobile_no = document.getElementById('reg_mobile_no').value.trim();
  const email = document.getElementById('reg_email').value.trim();
  const password = document.getElementById('reg_password').value;
  const confirm_password = document.getElementById('reg_confirm_password').value;

  if (password !== confirm_password) {
    showToast('Passwords do not match', 'error');
    if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = originalBtnText; }
    return;
  }

  try {
    const res = await fetch('/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, first_name, last_name, mobile_no, email, password, confirm_password })
    });
    
    if (res.ok) {
      const data = await res.json();
      showToast(data.message || 'Registration Successful!', 'success');
      setTimeout(() => window.location.href = data.redirect, 1200);
    } else {
      const errorText = await res.text();
      showToast(errorText || 'Registration failed', 'error');
      if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = originalBtnText; }
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
    if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = originalBtnText; }
  }
});

// Login Form Handler
document.getElementById('loginForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const submitBtn = this.querySelector('button[type="submit"]');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
  }

  const username = document.getElementById('login_username').value.trim();
  const password = document.getElementById('login_password').value;

  try {
    const res = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (res.ok) {
      const data = await res.json();
      showToast('Welcome back!', 'success');
      setTimeout(() => window.location.href = data.redirect, 800);
    } else {
      const err = await res.text();
      showToast(err || 'Invalid username or password', 'error');
      if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = 'Sign In <i class="fas fa-arrow-right"></i>'; }
    }
  } catch (err) {
    showToast('Error: ' + err.message, 'error');
    if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = 'Sign In <i class="fas fa-arrow-right"></i>'; }
  }
});

// Admin Login Form Handler
document.getElementById('adminLoginForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const username = document.getElementById('admin_username').value.trim();
  const password = document.getElementById('admin_password').value;

  try {
    const res = await fetch('/admin_auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (res.ok) {
      const data = await res.json();
      showToast('Admin Authentication Successful!', 'success');
      setTimeout(() => window.location.href = data.redirect, 800);
    } else {
      showToast(await res.text() || 'Invalid Admin Credentials', 'error');
    }
  } catch (err) {
    showToast('Error: ' + err.message, 'error');
  }
});