let clients = [];
let refreshInterval;
let statusChart = null;
let osChart = null;
let activityChart = null;
let adminClientKey = null;

function refreshClients() {
    fetch('/api/clients')
        .then(r => r.json())
        .then(data => {
            clients = data;
            renderStats();
            renderCharts();
            renderClients();
        })
        .catch(err => showToast('Failed to load clients: ' + err.message, 'danger'));
    fetch('/api/admin-client')
        .then(r => r.json())
        .then(data => {
            if (data.registered) adminClientKey = data.registration_key;
        })
        .catch(() => {});
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

function renderCharts() {
    const online = clients.filter(c => c.status === 'online').length;
    const offline = clients.filter(c => c.status === 'offline').length;
    const pending = clients.filter(c => c.status === 'pending' || !c.approved).length;

    if (!statusChart) {
        const ctx1 = document.getElementById('statusChart').getContext('2d');
        statusChart = new Chart(ctx1, {
            type: 'doughnut',
            data: {
                labels: ['Online', 'Offline', 'Pending'],
                datasets: [{
                    data: [online, offline, pending],
                    backgroundColor: ['#22c55e', '#ef4444', '#eab308'],
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#8888a0', padding: 12 } }
                }
            }
        });
    } else {
        statusChart.data.datasets[0].data = [online, offline, pending];
        statusChart.update();
    }

    const osCounts = {};
    clients.forEach(c => {
        const os = c.platform || 'Unknown';
        osCounts[os] = (osCounts[os] || 0) + 1;
    });
    const osLabels = Object.keys(osCounts);
    const osData = Object.values(osCounts);
    const osColors = ['#4f8cff', '#a78bfa', '#f472b6', '#34d399', '#fbbf24', '#f97316', '#8888a0'];

    if (!osChart) {
        const ctx2 = document.getElementById('osChart').getContext('2d');
        osChart = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: osLabels,
                datasets: [{
                    data: osData,
                    backgroundColor: osColors.slice(0, osLabels.length),
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#8888a0', padding: 12 } }
                }
            }
        });
    } else {
        osChart.data.labels = osLabels;
        osChart.data.datasets[0].data = osData;
        osChart.data.datasets[0].backgroundColor = osColors.slice(0, osLabels.length);
        osChart.update();
    }

    const now = new Date();
    const dayLabels = [];
    const dayCounts = [];
    for (let i = 6; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(d.getDate() - i);
        dayLabels.push(d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }));
        const dayStart = new Date(d);
        dayStart.setHours(0, 0, 0, 0);
        const dayEnd = new Date(d);
        dayEnd.setHours(23, 59, 59, 999);
        const count = clients.filter(c => {
            if (!c.last_seen) return false;
            const ls = new Date(c.last_seen);
            return ls >= dayStart && ls <= dayEnd;
        }).length;
        dayCounts.push(count);
    }

    if (!activityChart) {
        const ctx3 = document.getElementById('activityChart').getContext('2d');
        activityChart = new Chart(ctx3, {
            type: 'bar',
            data: {
                labels: dayLabels,
                datasets: [{
                    label: 'Active Clients',
                    data: dayCounts,
                    backgroundColor: '#4f8cff',
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        ticks: { color: '#8888a0', maxRotation: 45 },
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#8888a0', stepSize: 1 },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    }
                }
            }
        });
    } else {
        activityChart.data.labels = dayLabels;
        activityChart.data.datasets[0].data = dayCounts;
        activityChart.update();
    }
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
    const searchTerm = (document.getElementById('searchInput')?.value || '').toLowerCase();
    const statusFilter = document.getElementById('statusFilter')?.value || 'all';
    const filtered = clients.filter(c => {
        if (searchTerm && !c.hostname?.toLowerCase().includes(searchTerm) && !c.registration_key?.toLowerCase().includes(searchTerm) && !c.platform?.toLowerCase().includes(searchTerm)) return false;
        if (statusFilter === 'online' && c.status !== 'online') return false;
        if (statusFilter === 'offline' && c.status !== 'offline') return false;
        if (statusFilter === 'pending' && c.status !== 'pending' && c.approved !== false) return false;
        return true;
    });
    const filterCount = document.getElementById('filterCount');
    if (filterCount) filterCount.textContent = filtered.length < clients.length ? `Showing ${filtered.length} of ${clients.length}` : `${clients.length} client${clients.length !== 1 ? 's' : ''}`;
    grid.innerHTML = filtered.map(c => {
        const isAdmin = c.registration_key === adminClientKey;
        return `
        <div class="col-xl-3 col-lg-4 col-md-6 mb-3 client-card-wrapper">
            <div class="client-card p-3 ${isAdmin ? 'border-primary' : ''}" onclick="window.location='/client/${c.registration_key}'">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <span class="fw-semibold">${escapeHtml(c.hostname || 'Unknown')}</span>
                        <span class="badge bg-dark ms-1" style="font-family:monospace;font-size:0.7rem;">${c.registration_key}</span>
                        ${isAdmin ? '<span class="badge bg-primary ms-1">Admin</span>' : ''}
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        ${c.approved && !isAdmin ? `<button class="btn btn-sm btn-outline-info" onclick="event.stopPropagation();scanClient('${c.registration_key}')" title="Scan this client"><i class="bi bi-play-fill"></i></button>` : ''}
                        <span class="status-dot ${c.status === 'online' ? 'online' : c.status === 'pending' ? 'pending' : 'offline'}"></span>
                    </div>
                </div>
                <div class="small text-secondary">
                    <div>${c.platform || 'Unknown'}</div>
                    <div>Last seen: ${timeAgo(c.last_seen)}</div>
                    ${c.purchase_cost ? '<div>Cost: $' + parseFloat(c.purchase_cost).toFixed(2) + '</div>' : ''}
                </div>
                ${!c.approved ? '<div class="mt-2"><span class="badge bg-warning text-dark">Pending Approval</span></div>' : ''}
            </div>
        </div>`}).join('');
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

function filterClients() {
    renderClients();
}

function exportCSV() {
    if (clients.length === 0) {
        showToast('No clients to export', 'warning');
        return;
    }
    const headers = ['Hostname', 'Key', 'Platform', 'Status', 'Last Seen', 'Purchase Cost', 'Vendor', 'Notes'];
    const rows = clients.map(c => [
        c.hostname || '',
        c.registration_key,
        c.platform || '',
        c.status || '',
        c.last_seen || '',
        c.purchase_cost || '',
        c.vendor_name || '',
        (c.notes || '').replace(/"/g, '""'),
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.map(v => '"' + v + '"').join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'clients_export.csv';
    a.click();
    URL.revokeObjectURL(url);
    showToast('CSV exported!', 'success');
}

function scanAdminServer() {
    showToast('Scanning local server...', 'info');
    fetch('/api/scan/local', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'ok') {
                showToast('Server scan started! Refresh in a moment.', 'success');
                setTimeout(refreshClients, 3000);
            }
        })
        .catch(err => showToast('Error: ' + err.message, 'danger'));
}

function scanClient(key) {
    showToast('Scan triggered! Redirecting to detail page...', 'info');
    window.location.href = `/client/${key}`;
}

function scanAll() {
    showToast('Scanning all clients...', 'info');
    fetch('/api/scan/all', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'ok') {
                showToast(data.message || 'Scanning all clients!', 'success');
                setTimeout(refreshClients, 3000);
            } else {
                showToast('Error: ' + (data.message || 'Unknown'), 'danger');
            }
        })
        .catch(err => showToast('Error: ' + err.message, 'danger'));
}

refreshClients();
refreshInterval = setInterval(refreshClients, 5000);
