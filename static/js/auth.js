// Tab Switching
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tab + 'Tab').classList.add('active');
}

// Toggle Password
function togglePass(inputId, btn) {
    const input = document.getElementById(inputId);
    const icon = btn.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

// Password Strength Meter
const signupPass = document.getElementById('signupPass');
if (signupPass) {
    signupPass.addEventListener('input', function() {
        const p = this.value;
        const bar = document.getElementById('strengthBar');
        const text = document.getElementById('strengthText');
        
        let strength = 0;
        if (p.length >= 8) strength++;
        if (/[A-Z]/.test(p)) strength++;
        if (/[a-z]/.test(p)) strength++;
        if (/\d/.test(p)) strength++;
        
        const colors = ['#ef4444', '#f59e0b', '#f59e0b', '#10b981', '#10b981'];
        const texts = ['Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];
        
        bar.style.width = (strength * 25) + '%';
        bar.style.background = colors[strength];
        text.textContent = texts[strength];
        
        // Update requirement icons
        document.getElementById('req-len').querySelector('i').className = p.length >= 8 ? 'fas fa-check-circle' : 'fas fa-circle';
        document.getElementById('req-up').querySelector('i').className = /[A-Z]/.test(p) ? 'fas fa-check-circle' : 'fas fa-circle';
        document.getElementById('req-num').querySelector('i').className = /\d/.test(p) ? 'fas fa-check-circle' : 'fas fa-circle';
    });
}

// Form Validation
document.getElementById('loginForm')?.addEventListener('submit', function(e) {
    const email = this.querySelector('input[name="email"]').value.trim();
    const pass = this.querySelector('input[name="password"]').value;
    let valid = true;
    
    this.querySelectorAll('.error-msg').forEach(el => el.textContent = '');
    
    if (!email) {
        this.querySelector('input[name="email"]').parentElement.querySelector('.error-msg').textContent = 'Email required';
        valid = false;
    }
    if (!pass) {
        this.querySelector('input[name="password"]').parentElement.querySelector('.error-msg').textContent = 'Password required';
        valid = false;
    }
    if (!valid) e.preventDefault();
});

document.getElementById('signupForm')?.addEventListener('submit', function(e) {
    const pass = this.querySelector('input[name="password"]').value;
    const confirm = this.querySelector('input[name="confirm_password"]').value;
    let valid = true;
    
    this.querySelectorAll('.error-msg').forEach(el => el.textContent = '');
    
    if (pass !== confirm) {
        this.querySelector('input[name="confirm_password"]').parentElement.querySelector('.error-msg').textContent = 'Passwords do not match';
        valid = false;
    }
    if (!valid) e.preventDefault();
});