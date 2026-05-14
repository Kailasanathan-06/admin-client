let clients = [];
let refreshInterval;

function refreshClients() {
    fetch('/api/clients')
        .then(r => r.json())
        .then(data => {
            clients = data;
            renderStats();
            renderClients();
        })
        .catch(err => showToast('Failed to load clients: ' + err.message, 'danger'));
}

function renderStats() {
    const total = clients.length;
    const online = clients.filter(c => c.status === 'online').length;
    const offline = clients.filter(c => c.status === 'offline').length;
    const pending = clients.filter(c => c.status === 'pending' || !c.approved).length;
    document.getElementById('totalClients').textContent = total;
    document.getElementById('onlineClients').textContent = online;
    document.getElementById('offlineClients').textContent = offline;
    document.getElementById('pendingClients').textContent = pending;
}

function renderClients() {
    const grid = document.getElementById('clientGrid');
    if (clients.length === 0) {
        grid.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="bi bi-laptops fs-1 text-secondary"></i>
                <p class="text-secondary mt-3">No clients registered yet.<br>
                <small>Run the client app on any machine to get started.</small></p>
            </div>`;
        return;
    }
    grid.innerHTML = clients.map(c => `
        <div class="col-xl-3 col-lg-4 col-md-6 mb-3">
            <div class="client-card p-3" onclick="window.location='/client/${c.registration_key}'">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <span class="fw-semibold">${escapeHtml(c.hostname || 'Unknown')}</span>
                        <span class="badge bg-dark ms-1" style="font-family:monospace;font-size:0.7rem;">${c.registration_key}</span>
                    </div>
                    <span class="status-dot ${c.status === 'online' ? 'online' : c.status === 'pending' ? 'pending' : 'offline'}"></span>
                </div>
                <div class="small text-secondary">
                    <div>${c.platform || 'Unknown'}</div>
                    <div>Last seen: ${timeAgo(c.last_seen)}</div>
                    ${c.purchase_cost ? '<div>Cost: $' + parseFloat(c.purchase_cost).toFixed(2) + '</div>' : ''}
                </div>
                ${!c.approved ? '<div class="mt-2"><span class="badge bg-warning text-dark">Pending Approval</span></div>' : ''}
            </div>
        </div>
    `).join('');
}

function registerClient() {
    const key = document.getElementById('regKeyInput').value.trim().toUpperCase();
    if (!key || key.length < 4) {
        showToast('Please enter a valid registration key (4-8 characters)', 'warning');
        return;
    }
    fetch('/api/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ registration_key: key }),
    })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'ok') {
                showToast('Client registered successfully!', 'success');
                document.getElementById('regKeyInput').value = '';
                bootstrap.Modal.getInstance(document.getElementById('registerModal')).hide();
                refreshClients();
            } else {
                // Try registering first
                fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ registration_key: key, hostname: 'Manual', platform: 'Unknown' }),
                }).then(r => r.json()).then(() => {
                    fetch('/api/approve', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ registration_key: key }),
                    }).then(r2 => r2.json()).then(d2 => {
                        if (d2.status === 'ok') {
                            showToast('Client registered!', 'success');
                            bootstrap.Modal.getInstance(document.getElementById('registerModal')).hide();
                            refreshClients();
                        } else {
                            showToast('Error: ' + (d2.message || 'Unknown'), 'danger');
                        }
                    });
                });
            }
        })
        .catch(err => showToast('Error: ' + err.message, 'danger'));
}

refreshClients();
refreshInterval = setInterval(refreshClients, 5000);
