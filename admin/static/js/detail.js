let clientData = null;
let latestScan = null;

function loadClient() {
    fetch(`/api/clients/${CLIENT_KEY}`)
        .then(r => r.json())
        .then(data => {
            clientData = data;
            latestScan = (data.scans && data.scans.length > 0) ? data.scans[0] : null;
            renderClientInfo();
            renderSystem();
            renderManual();
            renderAddons();
            renderNetwork();
            renderSoftware();
            renderScanConfig();
        })
        .catch(err => showToast('Failed to load client: ' + err.message, 'danger'));
}

function renderClientInfo() {
    const h = document.getElementById('clientHostname');
    h.textContent = clientData.hostname || 'Unknown';
    document.getElementById('clientKey').textContent = clientData.registration_key;
    const badge = document.getElementById('clientStatusBadge');
    const status = clientData.status || 'offline';
    badge.textContent = status.toUpperCase();
    badge.className = 'badge ms-2 bg-' + (status === 'online' ? 'success' : status === 'pending' ? 'warning' : 'danger');
}

function renderSystem() {
    const container = document.getElementById('systemContent');
    if (!latestScan) {
        container.innerHTML = '<div class="col-12 text-center py-5 text-secondary">No scan data available yet.</div>';
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
                        <tr><td class="text-secondary">Serial</td><td><code>${escapeHtml(sd.ram?.serial || '-')}</code></td></tr>
                        <tr><td class="text-secondary">Frequency</td><td>${sd.ram?.frequency_mhz || 0} MHz</td></tr>
                        <tr><td class="text-secondary">Slot</td><td>${escapeHtml(sd.ram?.slot || '-')}</td></tr>
                        <tr><td class="text-secondary">Manufacturer</td><td>${escapeHtml(sd.ram?.manufacturer || '-')}</td></tr>
                    </table>
                </div>
            </div>
        </div>
        <div class="col-md-6 mb-3">
            <div class="card h-100">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-secondary"><i class="bi bi-device-hdd me-1"></i>Storage</h6>
                    ${(sd.storage?.disks || []).map(d => `
                        <div class="mb-2 p-2" style="background:rgba(255,255,255,0.03);border-radius:6px;">
                            <div class="small">${escapeHtml(d.model || 'Unknown')}</div>
                            <div class="small text-secondary">SN: ${escapeHtml(d.serial || '-')} | ${d.size_gb || 0} GB</div>
                        </div>
                    `).join('') || '<div class="text-secondary">No data</div>'}
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
                        <tr><td class="text-secondary">BIOS Version</td><td>${escapeHtml(sd.motherboard?.bios_version || '-')}</td></tr>
                        <tr><td class="text-secondary">BIOS Vendor</td><td>${escapeHtml(sd.motherboard?.bios_vendor || '-')}</td></tr>
                    </table>
                </div>
            </div>
        </div>
        <div class="col-md-6 mb-3">
            <div class="card h-100">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-secondary"><i class="bi bi-display me-1"></i>Graphics</h6>
                    ${(sd.gpu || []).map(g => `
                        <div class="mb-2 p-2" style="background:rgba(255,255,255,0.03);border-radius:6px;">
                            <div>${escapeHtml(g.name || 'Unknown')}</div>
                            <div class="small text-secondary">VRAM: ${g.vram_mb || 0} MB | Driver: ${escapeHtml(g.driver || '-')}</div>
                        </div>
                    `).join('') || '<div class="text-secondary">No data</div>'}
                </div>
            </div>
        </div>
        <div class="col-md-6 mb-3">
            <div class="card h-100">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-secondary"><i class="bi bi-windows me-1"></i>Operating System</h6>
                    <table class="table table-sm table-borderless">
                        <tr><td class="text-secondary">Type</td><td>${escapeHtml(sd.os_info?.system_type || '-')}</td></tr>
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
                    <h6 class="card-subtitle mb-2 text-secondary"><i class="bi bi-shield me-1"></i>Antivirus & Scan Info</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Antivirus:</strong>
                            ${(sd.antivirus?.products || []).map(a => escapeHtml(a.name)).join(', ') || 'None detected'}
                        </div>
                        <div class="col-md-3">
                            <strong>Scan Type:</strong> ${latestScan.scan_type || 'N/A'}
                        </div>
                        <div class="col-md-3">
                            <strong>Last Scan:</strong> ${timeAgo(latestScan.created_at)}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    container.innerHTML = html;
}

function renderManual() {
    if (!clientData) return;
    document.getElementById('manualCost').value = clientData.purchase_cost || '';
    document.getElementById('manualPurchaseDate').value = clientData.purchase_date || '';
    document.getElementById('manualWarranty').value = clientData.warranty_expiry || '';
    document.getElementById('manualVendor').value = clientData.vendor_name || '';
    document.getElementById('manualVendorContact').value = clientData.vendor_contact || '';
    document.getElementById('manualNotes').value = clientData.notes || '';
}

function saveManual() {
    const data = {
        purchase_cost: document.getElementById('manualCost').value ? parseFloat(document.getElementById('manualCost').value) : null,
        purchase_date: document.getElementById('manualPurchaseDate').value || null,
        warranty_expiry: document.getElementById('manualWarranty').value || null,
        vendor_name: document.getElementById('manualVendor').value || null,
        vendor_contact: document.getElementById('manualVendorContact').value || null,
        notes: document.getElementById('manualNotes').value || null,
    };
    fetch(`/api/clients/${CLIENT_KEY}/manual`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    })
        .then(r => r.json())
        .then(res => {
            if (res.status === 'ok') {
                showToast('Manual info saved!', 'success');
            } else {
                showToast('Error: ' + (res.message || 'Unknown'), 'danger');
            }
        });
}

function renderAddons() {
    const tbody = document.getElementById('addonsTableBody');
    const addons = clientData?.addons || [];
    if (addons.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-secondary">No add-on devices</td></tr>';
        return;
    }
    tbody.innerHTML = addons.map(a => `
        <tr>
            <td>${escapeHtml(a.name)}</td>
            <td>${escapeHtml(a.description || '')}</td>
            <td><code>${escapeHtml(a.serial_number || '')}</code></td>
            <td>${a.purchase_cost ? '$' + parseFloat(a.purchase_cost).toFixed(2) : '-'}</td>
            <td>${escapeHtml(a.category || '')}</td>
            <td><button class="btn btn-sm btn-outline-danger" onclick="deleteAddon(${a.id})"><i class="bi bi-trash"></i></button></td>
        </tr>
    `).join('');
}

function showAddAddonModal() {
    document.getElementById('addonName').value = '';
    document.getElementById('addonDesc').value = '';
    document.getElementById('addonSerial').value = '';
    document.getElementById('addonCost').value = '';
    document.getElementById('addonCategory').value = '';
    new bootstrap.Modal(document.getElementById('addAddonModal')).show();
}

function saveAddon() {
    const data = {
        name: document.getElementById('addonName').value.trim(),
        description: document.getElementById('addonDesc').value.trim(),
        serial_number: document.getElementById('addonSerial').value.trim(),
        purchase_cost: document.getElementById('addonCost').value ? parseFloat(document.getElementById('addonCost').value) : null,
        category: document.getElementById('addonCategory').value,
    };
    if (!data.name) {
        showToast('Device name is required', 'warning');
        return;
    }
    fetch(`/api/clients/${CLIENT_KEY}/addons`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    })
        .then(r => r.json())
        .then(res => {
            if (res.status === 'ok') {
                showToast('Add-on device added!', 'success');
                bootstrap.Modal.getInstance(document.getElementById('addAddonModal')).hide();
                loadClient();
            } else {
                showToast('Error: ' + (res.message || 'Unknown'), 'danger');
            }
        });
}

function deleteAddon(addonId) {
    if (!confirm('Delete this add-on device?')) return;
    fetch(`/api/clients/${CLIENT_KEY}/addons/${addonId}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(res => {
            if (res.status === 'ok') {
                showToast('Add-on deleted', 'success');
                loadClient();
            }
        });
}

function renderNetwork() {
    const tbody = document.getElementById('networkTableBody');
    const interfaces = latestScan?.scan_data?.network?.interfaces || [];
    if (interfaces.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-secondary">No network data</td></tr>';
        return;
    }
    tbody.innerHTML = interfaces.map(i => `
        <tr>
            <td>${escapeHtml(i.name || '')}</td>
            <td><code>${escapeHtml(i.mac || '')}</code></td>
            <td>${(i.ipv4 || []).join(', ') || '-'}</td>
            <td><span class="badge bg-${((i.ipv4 || []).length > 0) ? 'success' : 'secondary'}">${(i.ipv4 || []).length > 0 ? 'Active' : 'Inactive'}</span></td>
        </tr>
    `).join('');
}

function renderSoftware() {
    const tbody = document.getElementById('softwareTableBody');
    const software = latestScan?.scan_data?.software || [];
    if (software.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center text-secondary">No software data</td></tr>';
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
        (s.name || '').toLowerCase().includes(query) ||
        (s.publisher || '').toLowerCase().includes(query)
    );
    const tbody = document.getElementById('softwareTableBody');
    tbody.innerHTML = filtered.map(s => `
        <tr>
            <td>${escapeHtml(s.name)}</td>
            <td>${escapeHtml(s.version || '')}</td>
            <td>${escapeHtml(s.publisher || '')}</td>
        </tr>
    `).join('');
    document.getElementById('softwareCount').textContent = `Showing ${filtered.length} of ${window._softwareData.length} applications`;
}

function renderScanConfig() {
    fetch(`/api/clients/${CLIENT_KEY}/scan-config`)
        .then(r => r.json())
        .then(config => {
            document.getElementById('scanInterval').value = config.interval_seconds || 3600;
            document.getElementById('scanEnabled').checked = config.enabled !== false;
        });
}

function saveScanConfig() {
    const data = {
        interval_seconds: parseInt(document.getElementById('scanInterval').value),
        enabled: document.getElementById('scanEnabled').checked,
    };
    fetch(`/api/clients/${CLIENT_KEY}/scan-config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    })
        .then(r => r.json())
        .then(res => {
            if (res.status === 'ok') {
                showToast('Scan config saved!', 'success');
            }
        });
}

function triggerScan() {
    fetch(`/api/clients/${CLIENT_KEY}/scan-now`, { method: 'POST' })
        .then(r => r.json())
        .then(res => {
            if (res.status === 'ok') {
                showToast('Scan triggered! Client will pick up on next heartbeat.', 'success');
            }
        });
}

function deleteClient() {
    if (!confirm('Permanently delete this client and all data?')) return;
    fetch(`/api/clients/${CLIENT_KEY}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(res => {
            if (res.status === 'ok') {
                showToast('Client deleted', 'success');
                window.location.href = '/';
            }
        });
}

let detailRefreshInterval;

function startDetailRefresh() {
    if (detailRefreshInterval) clearInterval(detailRefreshInterval);
    detailRefreshInterval = setInterval(() => {
        if (latestScan) {
            clearInterval(detailRefreshInterval);
            return;
        }
        loadClient();
    }, 3000);
}

loadClient();
startDetailRefresh();
