document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            const btn = loginForm.querySelector('button');
            btn.innerHTML = 'Authenticating...';
            btn.disabled = true;

            try {
                const res = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                const data = await res.json();

                if (data.status === 'success') {
                    window.location.href = '/dashboard';
                } else {
                    alert('Authentication Failed');
                    btn.innerHTML = 'Authenticate';
                    btn.disabled = false;
                }
            } catch (err) {
                console.error(err);
                alert('Server Connection Error');
                btn.innerHTML = 'Authenticate';
                btn.disabled = false;
            }
        });
    }
});
