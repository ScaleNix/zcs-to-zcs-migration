// Zimbra Migration Tool - Frontend JavaScript

// Socket.IO connection
const socket = io();

// Application state
let appState = {
    accounts: [],
    migrationStatus: 'idle',
    config: {}
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeSocketListeners();
    loadConfiguration();
    checkMigrationStatus();

    // Show incremental date field when incremental migration is checked
    document.getElementById('incremental-migration').addEventListener('change', function() {
        document.getElementById('incremental-date-container').style.display =
            this.checked ? 'block' : 'none';
    });
});

// Navigation
function initializeNavigation() {
    const navItems = document.querySelectorAll('.list-group-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            showSection(section);

            // Update active state
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function showSection(sectionName) {
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
        section.style.display = 'none';
    });
    document.getElementById(`section-${sectionName}`).style.display = 'block';
}

// Socket.IO listeners
function initializeSocketListeners() {
    socket.on('connect', function() {
        updateConnectionStatus(true);
        showNotification('Connected to migration server', 'success');
    });

    socket.on('disconnect', function() {
        updateConnectionStatus(false);
        showNotification('Disconnected from server', 'warning');
    });

    socket.on('migration_state', function(data) {
        updateMigrationState(data);
    });

    socket.on('log_message', function(data) {
        appendLog(data);
    });

    socket.on('migration_complete', function(data) {
        showNotification('Migration completed successfully!', 'success');
        updateStatistics(data.statistics);
    });
}

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    if (connected) {
        statusEl.innerHTML = '<i class="bi bi-circle-fill text-success"></i> Connected';
    } else {
        statusEl.innerHTML = '<i class="bi bi-circle-fill text-danger"></i> Disconnected';
    }
}

// Configuration Management
async function loadConfiguration() {
    try {
        const response = await fetch('/api/config?path=config.ini');
        if (response.ok) {
            const config = await response.json();
            appState.config = config;
            populateConfigForms(config);
        }
    } catch (error) {
        console.error('Failed to load configuration:', error);
    }
}

function populateConfigForms(config) {
    if (config.zimbra_source) {
        populateForm('source-config-form', config.zimbra_source);
    }
    if (config.zimbra_destination) {
        populateForm('dest-config-form', config.zimbra_destination);
    }
    if (config.global) {
        populateForm('global-config-form', config.global);
    }
}

function populateForm(formId, data) {
    const form = document.getElementById(formId);
    if (!form) return;

    Object.keys(data).forEach(key => {
        const input = form.querySelector(`[name="${key}"]`);
        if (input) {
            input.value = data[key];
        }
    });
}

function getFormData(formId) {
    const form = document.getElementById(formId);
    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    return data;
}

async function saveConfiguration() {
    try {
        const sourceConfig = getFormData('source-config-form');
        const destConfig = getFormData('dest-config-form');
        const globalConfig = getFormData('global-config-form');

        const configData = {
            zimbra_source: sourceConfig,
            zimbra_destination: destConfig,
            global: globalConfig,
            config_path: 'config.ini'
        };

        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(configData)
        });

        const result = await response.json();
        if (result.success) {
            showNotification('Configuration saved successfully', 'success');
        } else {
            showNotification('Failed to save configuration: ' + result.error, 'danger');
        }
    } catch (error) {
        showNotification('Error saving configuration: ' + error.message, 'danger');
    }
}

async function validateConnection(type) {
    try {
        const response = await fetch('/api/validate-connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type: type })
        });

        const result = await response.json();
        if (result.success) {
            showNotification(result.message, 'success');
        } else {
            showNotification('Connection validation failed: ' + result.error, 'danger');
        }
    } catch (error) {
        showNotification('Error validating connection: ' + error.message, 'danger');
    }
}

// Account Loading
async function loadAccountsFromLDAP() {
    try {
        const ldapFilter = document.getElementById('ldap-filter').value;

        showLoadingIndicator();

        const response = await fetch('/api/accounts/ldap', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                config_path: 'config.ini',
                ldap_filter: ldapFilter || undefined
            })
        });

        const result = await response.json();
        hideLoadingIndicator();

        if (result.success) {
            appState.accounts = result.accounts;
            displayAccounts(result.accounts);
            updateQuickStats({ accounts: result.count });
            showNotification(`Loaded ${result.count} accounts from LDAP`, 'success');
        } else {
            showNotification('Failed to load accounts: ' + result.error, 'danger');
        }
    } catch (error) {
        hideLoadingIndicator();
        showNotification('Error loading accounts: ' + error.message, 'danger');
    }
}

async function loadAccountsFromCSV() {
    try {
        const csvPath = document.getElementById('csv-path').value;
        if (!csvPath) {
            showNotification('Please enter CSV file path', 'warning');
            return;
        }

        showLoadingIndicator();

        const response = await fetch('/api/accounts/csv', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                config_path: 'config.ini',
                csv_path: csvPath
            })
        });

        const result = await response.json();
        hideLoadingIndicator();

        if (result.success) {
            appState.accounts = result.accounts;
            displayAccounts(result.accounts);
            updateQuickStats({ accounts: result.count });
            showNotification(`Loaded ${result.count} accounts from CSV`, 'success');
        } else {
            showNotification('Failed to load accounts: ' + result.error, 'danger');
        }
    } catch (error) {
        hideLoadingIndicator();
        showNotification('Error loading accounts: ' + error.message, 'danger');
    }
}

function displayAccounts(accounts) {
    const container = document.getElementById('accounts-container');
    const tableBody = document.getElementById('accounts-table-body');
    const countEl = document.getElementById('accounts-count');

    tableBody.innerHTML = '';
    countEl.textContent = accounts.length;

    accounts.forEach((account, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td><strong>${account.email}</strong></td>
            <td><code>${account.folder}</code></td>
        `;
        tableBody.appendChild(row);
    });

    container.style.display = 'block';
}

// Migration Control
async function startMigration() {
    try {
        if (appState.accounts.length === 0) {
            showNotification('Please load accounts first', 'warning');
            return;
        }

        const fullMigration = document.getElementById('full-migration').checked;
        const incrMigration = document.getElementById('incremental-migration').checked;
        const ldiffMigration = document.getElementById('ldiff-migration').checked;

        if (!fullMigration && !incrMigration && !ldiffMigration) {
            showNotification('Please select at least one migration type', 'warning');
            return;
        }

        const threads = parseInt(document.getElementById('migration-threads').value);
        const storeIndex = parseInt(document.getElementById('store-index').value);
        const incrDate = document.getElementById('incremental-date').value;

        const migrationData = {
            config_path: 'config.ini',
            threads: threads,
            store_index: storeIndex,
            full_migration: fullMigration,
            incremental_migration: incrMigration,
            ldiff_migration: ldiffMigration,
            incremental_date: incrDate || undefined
        };

        const response = await fetch('/api/migration/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(migrationData)
        });

        const result = await response.json();
        if (result.success) {
            showNotification('Migration started', 'success');
            updateMigrationButtons(true);
            showSection('monitoring');
        } else {
            showNotification('Failed to start migration: ' + result.error, 'danger');
        }
    } catch (error) {
        showNotification('Error starting migration: ' + error.message, 'danger');
    }
}

async function stopMigration() {
    try {
        const response = await fetch('/api/migration/stop', {
            method: 'POST'
        });

        const result = await response.json();
        if (result.success) {
            showNotification('Migration stop requested', 'warning');
            updateMigrationButtons(false);
        }
    } catch (error) {
        showNotification('Error stopping migration: ' + error.message, 'danger');
    }
}

async function checkMigrationStatus() {
    try {
        const response = await fetch('/api/migration/status');
        const status = await response.json();
        updateMigrationState(status);
    } catch (error) {
        console.error('Failed to check migration status:', error);
    }
}

function updateMigrationState(state) {
    appState.migrationStatus = state.status;

    // Update status badge
    const statusBadge = document.getElementById('migration-status-badge');
    const statusClasses = {
        'idle': 'bg-secondary',
        'running': 'bg-primary pulse',
        'completed': 'bg-success',
        'error': 'bg-danger',
        'stopped': 'bg-warning'
    };
    statusBadge.className = `badge ${statusClasses[state.status] || 'bg-secondary'}`;
    statusBadge.textContent = state.status.charAt(0).toUpperCase() + state.status.slice(1);

    // Update progress bar
    const progressBar = document.getElementById('migration-progress-bar');
    progressBar.style.width = state.progress + '%';
    progressBar.textContent = Math.round(state.progress) + '%';

    // Update processed accounts
    document.getElementById('accounts-processed').textContent = state.processed_accounts || 0;
    document.getElementById('accounts-total').textContent = state.total_accounts || 0;

    // Update current account
    if (state.current_account) {
        document.getElementById('current-account-container').style.display = 'block';
        document.getElementById('current-account-email').textContent = state.current_account;
    } else {
        document.getElementById('current-account-container').style.display = 'none';
    }

    // Update timing
    if (state.start_time) {
        document.getElementById('migration-start-time').textContent =
            new Date(state.start_time).toLocaleString();
    }
    if (state.end_time) {
        document.getElementById('migration-end-time').textContent =
            new Date(state.end_time).toLocaleString();
    }

    // Update errors
    if (state.errors && state.errors.length > 0) {
        document.getElementById('errors-container').style.display = 'block';
        document.getElementById('errors-list').innerHTML =
            state.errors.map(err => `<div>${err}</div>`).join('');
    } else {
        document.getElementById('errors-container').style.display = 'none';
    }

    // Update buttons
    updateMigrationButtons(state.status === 'running');

    // Update quick stats
    updateQuickStats({
        status: state.status,
        progress: Math.round(state.progress) + '%'
    });
}

function updateMigrationButtons(isRunning) {
    const startBtn = document.getElementById('start-migration-btn');
    const stopBtn = document.getElementById('stop-migration-btn');

    if (isRunning) {
        startBtn.disabled = true;
        stopBtn.disabled = false;
    } else {
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
}

// Statistics
async function updateStatistics(stats) {
    if (stats) {
        document.getElementById('stat-full-migrated').textContent = stats.full_migrated || 0;
        document.getElementById('stat-incr-migrated').textContent = stats.incr_migrated || 0;
        document.getElementById('stat-ldiff-migrated').textContent = stats.ldiff_imported || 0;
    } else {
        try {
            const response = await fetch('/api/statistics');
            const result = await response.json();
            if (result.success) {
                const s = result.statistics;
                document.getElementById('stat-full-migrated').textContent = s.full_migrated || 0;
                document.getElementById('stat-incr-migrated').textContent = s.incr_migrated || 0;
                document.getElementById('stat-ldiff-migrated').textContent = s.ldiff_imported || 0;
            }
        } catch (error) {
            console.error('Failed to fetch statistics:', error);
        }
    }
}

// Stores
async function listStores() {
    try {
        const response = await fetch('/api/stores?config_path=config.ini');
        const result = await response.json();

        if (result.success) {
            const storesHtml = result.stores.map(store =>
                `[${store.index}] ${store.name}`
            ).join('<br>');
            showNotification('Available Stores:<br>' + storesHtml, 'info', 5000);
        } else {
            showNotification('Failed to list stores: ' + result.error, 'danger');
        }
    } catch (error) {
        showNotification('Error listing stores: ' + error.message, 'danger');
    }
}

// Logs
function appendLog(logEntry) {
    const logsContent = document.getElementById('logs-content');
    const logEl = document.createElement('div');
    logEl.className = `log-entry ${logEntry.level}`;

    const timestamp = new Date(logEntry.timestamp).toLocaleTimeString();
    logEl.innerHTML = `<span class="log-timestamp">[${timestamp}]</span> <span class="log-level">[${logEntry.level}]</span> ${escapeHtml(logEntry.message)}`;

    // Clear initial message
    if (logsContent.textContent.includes('Waiting for log messages')) {
        logsContent.innerHTML = '';
    }

    logsContent.appendChild(logEl);

    // Auto-scroll to bottom
    const logsContainer = document.getElementById('logs-container');
    logsContainer.scrollTop = logsContainer.scrollHeight;

    // Keep only last 500 log entries
    const logEntries = logsContent.querySelectorAll('.log-entry');
    if (logEntries.length > 500) {
        logEntries[0].remove();
    }
}

function clearLogs() {
    document.getElementById('logs-content').innerHTML = 'Logs cleared. Waiting for new log messages...';
}

// Quick Stats
function updateQuickStats(updates) {
    if (updates.accounts !== undefined) {
        document.getElementById('stat-accounts').textContent = updates.accounts;
    }
    if (updates.status !== undefined) {
        document.getElementById('stat-status').textContent =
            updates.status.charAt(0).toUpperCase() + updates.status.slice(1);
    }
    if (updates.progress !== undefined) {
        document.getElementById('stat-progress').textContent = updates.progress;
    }
}

// Notifications
function showNotification(message, type = 'info', duration = 3000) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 150);
    }, duration);
}

// Loading Indicator
function showLoadingIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'loading-indicator';
    indicator.className = 'position-fixed top-50 start-50 translate-middle';
    indicator.style.zIndex = '9999';
    indicator.innerHTML = `
        <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    document.body.appendChild(indicator);
}

function hideLoadingIndicator() {
    const indicator = document.getElementById('loading-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Utility Functions
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Periodic status updates when migration is running
setInterval(() => {
    if (appState.migrationStatus === 'running') {
        checkMigrationStatus();
    }
}, 5000);
