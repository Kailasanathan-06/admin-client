let settings = {};
let groups = [];

function loadSettings() {
    Promise.all([
        fetch('/api/settings').then(r => r.json()),
        fetch('/api/groups').then(r => r.json()).catch(() => []),
        fetch('/api/clients').then(r => r.json()).catch(() => []),
    ]).then(([s, g, clients]) => {
        settings = s;
        groups = g;
        document.getElementById('autoApprove').checked = s.auto_approve || false;
        document.getElementById('staleThreshold').value = s.stale_threshold_seconds || 7200;
        document.getElementById('defaultScanInterval').value = s.scan_all_interval || 86400;
        document.getElementById('adminClientKey').textContent = s.admin_client_key || 'N/A';

        let totalScans = 0;
        clients.forEach(c => {
            if (c._scan_count) totalScans += c._scan_count;
        });
        document.getElementById('totalScans').textContent = clients.reduce((sum, c) => sum + (c._scan_count || 0), 0) || 'N/A';

        renderGroups();
    });
}

function saveSettings() {
    fetch('/api/settings', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            auto_approve: document.getElementById('autoApprove').checked,
            stale_threshold_seconds: parseInt(document.getElementById('staleThreshold').value),
            scan_all_interval: parseInt(document.getElementById('defaultScanInterval').value),
        })
    }).then(r => r.json()).then(res => {
        if (res.status === 'ok') showToast('Settings saved!', 'success');
    });
}

function scanAdminServer() {
    showToast('Scanning server...', 'info');
    fetch('/api/scan/local', { method: 'POST' }).then(r => r.json()).then(() => {
        showToast('Server scan started!', 'success');
    });
}

function renderGroups() {
    const container = document.getElementById('groupsList');
    if (groups.length === 0) {
        container.innerHTML = '<div class="text-secondary small">No groups created yet</div>';
        return;
    }
    container.innerHTML = groups.map(g => `<div class="d-flex justify-content-between align-items-center p-2 mb-2 rounded" style="background:rgba(255,255,255,0.05);">
        <div>
            <strong>${escapeHtml(g.name)}</strong>
            <span class="text-secondary small ms-2">${g.client_count || 0} clients</span>
            ${g.description ? '<div class="small text-secondary">' + escapeHtml(g.description) + '</div>' : ''}
        </div>
        <button class="btn btn-sm btn-outline-danger" onclick="deleteGroup(${g.id})"><i class="bi bi-trash"></i></button>
    </div>`).join('');
}

function createGroup() {
    const name = document.getElementById('newGroupName').value.trim();
    if (!name) { showToast('Enter a group name', 'warning'); return; }
    fetch('/api/groups', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
    }).then(r => r.json()).then(() => {
        document.getElementById('newGroupName').value = '';
        showToast('Group created!', 'success');
        loadSettings();
    });
}

function deleteGroup(id) {
    if (!confirm('Delete this group? Clients will be ungrouped.')) return;
    fetch(`/api/groups/${id}`, { method: 'DELETE' }).then(r => r.json()).then(() => {
        showToast('Group deleted', 'success');
        loadSettings();
    });
}

function exportBackup() {
    showToast('Preparing backup...', 'info');
    Promise.all([
        fetch('/api/clients').then(r => r.json()),
        fetch('/api/groups').then(r => r.json()),
        fetch('/api/activity-log?limit=500').then(r => r.json()),
    ]).then(([clients, groups, logs]) => {
        const data = { export_date: new Date().toISOString(), clients, groups, activity_logs: logs };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = `scanner_backup_${new Date().toISOString().slice(0, 10)}.json`; a.click();
        URL.revokeObjectURL(url);
        showToast('Backup exported!', 'success');
    });
}

loadSettings();
