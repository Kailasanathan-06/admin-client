let clientData = null;
let latestScan = null;
let groups = [];
let scanTriggerPoll = null;
let detailRefreshInterval;

function loadClient() {
    Promise.all([
        fetch(`/api/clients/${CLIENT_KEY}`).then(r => r.json()),
        fetch('/api/groups').then(r => r.json()).catch(() => []),
    ]).then(([data, groupsData]) => {
        clientData = data;
        groups = groupsData;
        latestScan = (data.scans && data.scans.length > 0) ? data.scans[0] : null;
        renderClientInfo();
        renderChanges();
        renderSystem();
        renderManual();
        renderAddons();
        renderNetwork();
        renderPeripherals();
        renderSoftware();
        renderScanConfig();
    }).catch(err => showToast('Failed to load client: ' + err.message, 'danger'));
}

function renderClientInfo() {
    const h = document.getElementById('clientHostname');
    h.textContent = clientData.hostname || 'Unknown';
    document.getElementById('clientKey').textContent = clientData.registration_key;
    const badge = document.getElementById('clientStatusBadge');
    const status = clientData.status || 'offline';
    badge.textContent = (clientData.is_stale ? 'STALE' : status.toUpperCase());
    badge.className = 'badge ms-2 bg-' + (clientData.is_stale ? 'danger' : status === 'online' ? 'success' : status === 'pending' ? 'warning' : 'danger');

    const groupEl = document.getElementById('clientGroup');
    if (clientData.group_name) {
        groupEl.textContent = clientData.group_name;
        groupEl.style.display = '';
    } else {
        groupEl.style.display = 'none';
    }
}

function renderChanges() {
    const container = document.getElementById('changesContainer');
    const list = document.getElementById('changesList');
    const count = document.getElementById('changesCount');
    const changes = clientData?.scan_changes || [];
    if (changes.length === 0) { container.style.display = 'none'; return; }
    container.style.display = '';
    count.textContent = changes.length;
    list.innerHTML = changes.map(c => {
        const isAdd = c.startsWith('+ ');
        const isRemove = c.startsWith('\u2212 ');
        let icon = 'bi-arrow-right-short';
        let color = 'text-secondary';
        if (isAdd) { icon = 'bi-plus-circle text-success'; color = 'text-success'; }
        else if (isRemove) { icon = 'bi-dash-circle text-danger'; color = 'text-danger'; }
        return `<div class="small mb-1 ${color}"><i class="bi ${icon} me-1"></i>${escapeHtml(c)}</div>`;
    }).join('');
}

function renderSystem() {
    const container = document.getElementById('systemContent');
    if (!latestScan) {
        container.innerHTML = '<div class="col-12 text-center py-5 text-secondary">No scan data available. Run a scan from the client or click "Scan Now".</div>';
        return;
    }
    const sd = latestScan.scan_data || {};
    const html = `
        <div class="col-md-6 mb-3">
            <div class="card h-100">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-secondary"><i class="bi bi-cpu me-1"></i>Processor</h6>
                    <table class="table table-sm table-borderless">
                        <tr><td class="text-secondary">Model</td><td>${escapeHtml(sd.processor?.model || '-')}</td></tr>
                        <tr><td class="text-secondary">Manufacturer</td><td>${escapeHtml(sd.processor?.manufacturer || '-')}</td></tr>
                        <tr><td class="text-secondary">Serial</td><td><code>${escapeHtml(sd.processor?.serial || '-')}</code></td></tr>
                        <tr><td class="text-secondary">Cores</td><td>${sd.processor?.cores || 0} physical / ${sd.processor?.logical || 0} logical</td></tr>
                        <tr><td class="text-secondary">Speed</td><td>${sd.processor?.speed_mhz || 0} MHz</td></tr>
                        <tr><td class="text-secondary">Architecture</td><td>${escapeHtml(sd.processor?.architecture || '-')}</td></tr>
                    </table>
                </div>
            </div>
        </div>
        <div class="col-md-6 mb-3">
            <div class="card h-100">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-secondary"><i class="bi bi-memory me-1"></i>Memory</h6>
                    <table class="table table-sm table-borderless">
                        <tr><td class="text-secondary">Capacity</td><td>${escapeHtml(sd.ram?.capacity_gb || '-')}</td></tr>
                        <tr><td class="text-secondary">Manufacturer</td><td>${escapeHtml(sd.ram?.manufacturer || '-')}</td></tr>
                        <tr><td class="text-secondary">Serial</td><td><code>${escapeHtml(sd.ram?.serial || '-')}</code></td></tr>
                        <tr><td class="text-secondary">Frequency</td><td>${sd.ram?.frequency_mhz || 0} MHz</td></tr>
                        <tr><td class="text-secondary">Slot</td><td>${escapeHtml(sd.ram?.slot || '-')}</td></tr>
                    </table>
                </div>
            </div>
        </div>
        <div class="col-md-6 mb-3">
            <div class="card h-100">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-secondary"><i class="bi bi-device-hdd me-1"></i>Storage</h6>
                    ${(sd.storage?.disks || []).map(d => `<div class="mb-2 p-2" style="background:rgba(255,255,255,0.03);border-radius:6px;">
                        <div class="small">${escapeHtml(d.model || 'Unknown')}</div>
                        <div class="small text-secondary">SN: ${escapeHtml(d.serial || '-')} | ${d.size_gb || 0} GB</div>
                    </div>`).join('') || '<div class="text-secondary">No data</div>'}
                    ${((sd.storage?.partitions || []).map(p => `<div class="small text-secondary">${p.device} (${p.filesystem}): ${p.free_gb || 0} / ${p.total_gb || 0} GB free</div>`).join('') || ''}
                </div>
            </div>
        </div>
        <div class="col-md-6 mb-3">
            <div class="card h-100">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-secondary"><i class="bi bi-motherboard me-1"></i>Motherboard</h6>
                    <table class="table table-sm table-borderless">
                        <tr><td class="text-secondary">Manufacturer</td><td>${escapeHtml(sd.motherboard?.manufacturer || '-')}</td></tr>
                        <tr><td class="text-secondary">Product</td><td>${escapeHtml(sd.motherboard?.product || '-')}</td></tr>
                        <tr><td class="text-secondary">Serial</td><td><code>${escapeHtml(sd.motherboard?.serial || '-')}</code></td></tr>
                        <tr><td class="text-secondary">BIOS</td><td>${escapeHtml(sd.motherboard?.bios_vendor || '-')} ${escapeHtml(sd.motherboard?.bios_version || '')}</td></tr>
                    </table>
                </div>
            </div>
        </div>
        <div class="col-md-6 mb-3">
            <div class="card h-100">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-secondary"><i class="bi bi-display me-1"></i>Graphics</h6>
                    ${(sd.gpu || []).map(g => `<div class="mb-2 p-2" style="background:rgba(255,255,255,0.03);border-radius:6px;">
                        <div>${escapeHtml(g.name || 'Unknown')}</div>
                        <div class="small text-secondary">VRAM: ${g.vram_mb || 0} MB | Driver: ${escapeHtml(g.driver || '-')}</div>
                    </div>`).join('') || '<div class="text-secondary">No data</div>'}
                </div>
            </div>
        </div>
        <div class="col-md-6 mb-3">
            <div class="card h-100">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-secondary"><i class="bi bi-windows me-1"></i>Operating System</h6>
                    <table class="table table-sm table-borderless">
                        <tr><td class="text-secondary">Version</td><td>${escapeHtml(sd.os_info?.version || '-')}</td></tr>
                        <tr><td class="text-secondary">Build</td><td>${escapeHtml(sd.os_info?.build || '-')}</td></tr>
                        <tr><td class="text-secondary">Architecture</td><td>${escapeHtml(sd.os_info?.architecture || '-')}</td></tr>
                        <tr><td class="text-secondary">Hostname</td><td>${escapeHtml(sd.os_info?.hostname || '-')}</td></tr>
                    </table>
                </div>
            </div>
        </div>
        <div class="col-12 mb-3">
            <div class="card">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-secondary"><i class="bi bi-shield me-1"></i>Info</h6>
                    <div class="row">
                        <div class="col-md-3"><strong>Antivirus:</strong> ${(sd.antivirus?.products || []).map(a => escapeHtml(a.name)).join(', ') || 'None'}</div>
                        <div class="col-md-2"><strong>Type:</strong> ${latestScan.scan_type || 'N/A'}</div>
                        <div class="col-md-2"><strong>Source:</strong> ${sd.scanned_by === 'client_agent' ? '<span class="badge bg-success mt-1">Client</span>' : '<span class="badge bg-warning text-dark mt-1">Admin Local</span>'}</div>
                        <div class="col-md-2"><strong>Last Scan:</strong> ${timeAgo(latestScan.created_at)}</div>
                        <div class="col-md-3 d-flex align-items-center"><button class="btn btn-sm btn-outline-info w-100" onclick="triggerScan()"><i class="bi bi-play-fill"></i> Scan Now</button></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    container.innerHTML = html;
}

function renderManual() {
    if (!clientData) return;
    document.getElementById('manualHostname').value = clientData.hostname || '';
    document.getElementById('manualCost').value = clientData.purchase_cost || '';
    document.getElementById('manualPurchaseDate').value = clientData.purchase_date || '';
    document.getElementById('manualWarranty').value = clientData.warranty_expiry || '';
    document.getElementById('manualVendor').value = clientData.vendor_name || '';
    document.getElementById('manualVendorContact').value = clientData.vendor_contact || '';
    document.getElementById('manualNotes').value = clientData.notes || '';
    document.getElementById('manualTags').value = clientData.tags || '';

    const sel = document.getElementById('manualGroup');
    sel.innerHTML = '<option value="">No Group</option>' + groups.map(g => `<option value="${g.id}" ${clientData.group === g.id ? 'selected' : ''}>${escapeHtml(g.name)}</option>`).join('');
}

function saveManual() {
    const data = {
        hostname: document.getElementById('manualHostname').value || null,
        purchase_cost: document.getElementById('manualCost').value ? parseFloat(document.getElementById('manualCost').value) : null,
        purchase_date: document.getElementById('manualPurchaseDate').value || null,
        warranty_expiry: document.getElementById('manualWarranty').value || null,
        vendor_name: document.getElementById('manualVendor').value || null,
        vendor_contact: document.getElementById('manualVendorContact').value || null,
        notes: document.getElementById('manualNotes').value || null,
        group: document.getElementById('manualGroup').value || null,
        tags: document.getElementById('manualTags').value || '',
    };
    fetch(`/api/clients/${CLIENT_KEY}/manual`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
    }).then(r => r.json()).then(res => {
        if (res.status === 'ok') { showToast('Saved!', 'success'); loadClient(); }
        else { showToast('Error: ' + (res.message || 'Unknown'), 'danger'); }
    });
}

function renderAddons() {
    const tbody = document.getElementById('addonsTableBody');
    const addons = clientData?.addons || [];
    if (addons.length === 0) { tbody.innerHTML = '<tr><td colspan="6" class="text-center text-secondary">No add-on devices</td></tr>'; return; }
    tbody.innerHTML = addons.map(a => `<tr>
        <td>${escapeHtml(a.name)}</td>
        <td>${escapeHtml(a.description || '')}</td>
        <td><code>${escapeHtml(a.serial_number || '')}</code></td>
        <td>${a.purchase_cost ? '$' + parseFloat(a.purchase_cost).toFixed(2) : '-'}</td>
        <td>${escapeHtml(a.category || '')}</td>
        <td><button class="btn btn-sm btn-outline-danger" onclick="deleteAddon(${a.id})"><i class="bi bi-trash"></i></button></td>
    </tr>`).join('');
}

function showAddAddonModal() {
    ['addonName', 'addonDesc', 'addonSerial', 'addonCost'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('addonCategory').value = '';
    new bootstrap.Modal(document.getElementById('addAddonModal')).show();
}

function saveAddon() {
    const name = document.getElementById('addonName').value.trim();
    if (!name) { showToast('Device name is required', 'warning'); return; }
    const data = {
        name, description: document.getElementById('addonDesc').value.trim(),
        serial_number: document.getElementById('addonSerial').value.trim(),
        purchase_cost: document.getElementById('addonCost').value ? parseFloat(document.getElementById('addonCost').value) : null,
        category: document.getElementById('addonCategory').value,
    };
    fetch(`/api/clients/${CLIENT_KEY}/addons`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
    }).then(r => r.json()).then(res => {
        if (res.status === 'ok') {
            showToast('Device added!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('addAddonModal')).hide();
            loadClient();
        }
    });
}

function deleteAddon(addonId) {
    if (!confirm('Delete this device?')) return;
    fetch(`/api/clients/${CLIENT_KEY}/addons/${addonId}`, { method: 'DELETE' }).then(r => r.json()).then(res => {
        if (res.status === 'ok') { showToast('Deleted', 'success'); loadClient(); }
    });
}

function renderNetwork() {
    const tbody = document.getElementById('networkTableBody');
    const interfaces = latestScan?.scan_data?.network?.interfaces || [];
    if (interfaces.length === 0) { tbody.innerHTML = '<tr><td colspan="4" class="text-center text-secondary">No network data</td></tr>'; return; }
    tbody.innerHTML = interfaces.map(i => `<tr>
        <td>${escapeHtml(i.name || '')}</td>
        <td><code>${escapeHtml(i.mac || '')}</code></td>
        <td>${(i.ipv4 || []).join(', ') || '-'}</td>
        <td><span class="badge bg-${((i.ipv4 || []).length > 0) ? 'success' : 'secondary'}">${(i.ipv4 || []).length > 0 ? 'Active' : 'Inactive'}</span></td>
    </tr>`).join('');
}

function renderPeripherals() {
    const container = document.getElementById('peripheralsContent');
    const per = latestScan?.scan_data?.peripherals || {};
    const categories = [
        {key: 'keyboard', icon: 'bi-keyboard', label: 'Keyboards'},
        {key: 'mouse', icon: 'bi-mouse', label: 'Mice'},
        {key: 'printers', icon: 'bi-printer', label: 'Printers'},
        {key: 'storage', icon: 'bi-device-hdd', label: 'USB Storage'},
        {key: 'audio', icon: 'bi-speaker', label: 'Audio Devices'},
        {key: 'webcam', icon: 'bi-camera', label: 'Webcams'},
        {key: 'other_usb', icon: 'bi-plug', label: 'Other USB Devices'},
    ];
    let hasDevices = false;
    let html = '';
    for (const cat of categories) {
        const devices = per[cat.key] || [];
        if (devices.length === 0) continue;
        hasDevices = true;
        html += `<div class="mb-4"><h6 class="text-secondary mb-2"><i class="bi ${cat.icon} me-1"></i>${cat.label} (${devices.length})</h6>
            <div class="table-responsive"><table class="table table-dark table-hover table-sm"><thead><tr>
                <th>Name</th><th>Manufacturer</th><th>Description</th>
                ${cat.key === 'storage' ? '<th>Serial</th><th>Size</th>' : ''}
                <th>Status</th><th>Connection</th>
            </tr></thead><tbody>
            ${devices.map(d => {
                let detailRow = '';
                if (cat.key === 'storage') detailRow = `<td><code>${escapeHtml(d.serial || '')}</code></td><td>${d.size_gb ? d.size_gb + ' GB' : '-'}</td>`;
                const status = d.status || 'Unknown';
                return `<tr><td>${escapeHtml(d.name || '')}</td><td>${escapeHtml(d.manufacturer || '-')}</td><td>${escapeHtml(d.description || '-')}</td>${detailRow}<td><span class="badge ${status === 'OK' || status === 'connected' ? 'bg-success' : 'bg-secondary'}">${escapeHtml(status)}</span></td><td>${d.usb ? '<span class="badge bg-info">USB</span>' : '<span class="badge bg-secondary">Internal</span>'}</td></tr>`;
            }).join('')}
            </tbody></table></div></div>`;
    }
    container.innerHTML = hasDevices ? html : '<div class="text-center py-5 text-secondary">No peripherals detected</div>';
}

function renderSoftware() {
    const software = latestScan?.scan_data?.software || [];
    if (software.length === 0) {
        document.getElementById('softwareTableBody').innerHTML = '<tr><td colspan="3" class="text-center text-secondary">No software data</td></tr>';
        document.getElementById('softwareCount').textContent = '';
        return;
    }
    window._softwareData = software;
    document.getElementById('softwareCount').textContent = `Showing ${software.length} applications`;
    filterSoftware();
}

function filterSoftware() {
    const query = (document.getElementById('softwareSearch').value || '').toLowerCase();
    const filtered = (window._softwareData || []).filter(s =>
        (s.name || '').toLowerCase().includes(query) || (s.publisher || '').toLowerCase().includes(query)
    );
    document.getElementById('softwareTableBody').innerHTML = filtered.map(s => `<tr>
        <td>${escapeHtml(s.name)}</td><td>${escapeHtml(s.version || '')}</td><td>${escapeHtml(s.publisher || '')}</td>
    </tr>`).join('');
    document.getElementById('softwareCount').textContent = `Showing ${filtered.length} of ${window._softwareData.length} applications`;
}

function renderScanConfig() {
    fetch(`/api/clients/${CLIENT_KEY}/scan-config`).then(r => r.json()).then(config => {
        document.getElementById('scanInterval').value = config.interval_seconds || 3600;
        document.getElementById('scanEnabled').checked = config.enabled !== false;
    });
}

function saveScanConfig() {
    fetch(`/api/clients/${CLIENT_KEY}/scan-config`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interval_seconds: parseInt(document.getElementById('scanInterval').value), enabled: document.getElementById('scanEnabled').checked })
    }).then(r => r.json()).then(res => { if (res.status === 'ok') showToast('Scan config saved!', 'success'); });
}

function triggerScan() {
    showToast('Scan requested — waiting for client...', 'info');
    fetch(`/api/clients/${CLIENT_KEY}/scan-now`, { method: 'POST' })
        .then(r => r.json())
        .then(res => {
            if (res.status === 'ok') {
                const oldId = latestScan?.id || null;
                let attempts = 0;
                if (scanTriggerPoll) clearInterval(scanTriggerPoll);
                scanTriggerPoll = setInterval(() => {
                    attempts++;
                    if (attempts > 40) { clearInterval(scanTriggerPoll); scanTriggerPoll = null; loadClient(); showToast('Timed out. Check if the client agent is running.', 'warning'); return; }
                    fetch(`/api/clients/${CLIENT_KEY}`).then(r => r.json()).then(data => {
                        const newScan = (data.scans && data.scans.length > 0) ? data.scans[0] : null;
                        if (newScan && newScan.id !== oldId) {
                            clearInterval(scanTriggerPoll); scanTriggerPoll = null;
                            clientData = data; latestScan = newScan;
                            renderClientInfo(); renderChanges(); renderSystem(); renderNetwork(); renderPeripherals(); renderSoftware();
                            showToast('New scan data received from client!', 'success');
                        }
                    }).catch(() => {});
                }, 3000);
            } else { showToast('Error: ' + (res.message || 'Unknown'), 'danger'); }
        })
        .catch(err => showToast('Error: ' + err.message, 'danger'));
}

function deleteClient() {
    if (!confirm('Permanently delete this client and all data?')) return;
    fetch(`/api/clients/${CLIENT_KEY}`, { method: 'DELETE' }).then(r => r.json()).then(res => {
        if (res.status === 'ok') { showToast('Client deleted', 'success'); window.location.href = '/'; }
    });
}

function startDetailRefresh() {
    if (detailRefreshInterval) clearInterval(detailRefreshInterval);
    detailRefreshInterval = setInterval(loadClient, 10000);
}

loadClient();
startDetailRefresh();
