// Registration
document.getElementById('registrationForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('reg_username').value.trim();
    const first_name = document.getElementById('reg_first_name').value.trim();
    const last_name = document.getElementById('reg_last_name').value.trim();
    const mobile_no = document.getElementById('reg_mobile_no').value.trim();
    const email = document.getElementById('reg_email').value.trim();
    const password = document.getElementById('reg_password').value;
    const confirm_password = document.getElementById('reg_confirm_password').value;

    // Validation
    if (!username || !first_name || !last_name || !mobile_no || !email || !password || !confirm_password) {
        alert('All fields are required');
        return;
    }

    if (password !== confirm_password) {
        alert('Passwords do not match');
        return;
    }

    if (password.length < 8) {
        alert('Password must be at least 8 characters long');
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
            alert(data.message);
            window.location.href = data.redirect;
        } else {
            const errorText = await res.text();
            alert('Error: ' + errorText);
        }
    } catch (err) {
        alert('Error: ' + err.message);
    }
});

// Login
document.getElementById('loginForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
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
            alert(data.message);
            window.location.href = data.redirect;
        } else {
            alert(await res.text());
        }
    } catch (err) {
        alert('Error: ' + err.message);
    }
});

// Admin login
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
            alert(data.message);
            window.location.href = data.redirect;
        } else {
            alert(await res.text());
        }
    } catch (err) {
        alert('Error: ' + err.message);
    }
});