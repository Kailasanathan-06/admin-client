function changePassword() {
    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const errorDiv = document.getElementById('passwordError');

    errorDiv.classList.add('d-none');

    if (!oldPassword || !newPassword || !confirmPassword) {
        errorDiv.textContent = 'All fields are required';
        errorDiv.classList.remove('d-none');
        return;
    }

    if (newPassword !== confirmPassword) {
        errorDiv.textContent = 'New passwords do not match';
        errorDiv.classList.remove('d-none');
        return;
    }

    if (newPassword.length < 4) {
        errorDiv.textContent = 'Password must be at least 4 characters';
        errorDiv.classList.remove('d-none');
        return;
    }

    const userIdEl = document.querySelector('[data-user-id]');
    const userId = userIdEl ? userIdEl.dataset.userId : null;

    fetch('/api/admin/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            old_password: oldPassword,
            new_password: newPassword,
        }),
    }).then(r => r.json()).then(res => {
        if (res.status === 'ok') {
            showToast('Password updated successfully!', 'success');
            document.getElementById('oldPassword').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('confirmPassword').value = '';
        } else {
            errorDiv.textContent = res.message || 'Failed to update password';
            errorDiv.classList.remove('d-none');
        }
    }).catch(() => {
        errorDiv.textContent = 'An error occurred';
        errorDiv.classList.remove('d-none');
    });
}