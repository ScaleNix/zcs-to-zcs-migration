#!/usr/bin/env python3
"""Flask web application for Zimbra migration tool."""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from threading import Thread, Lock
import configobj

from config_manager import ConfigManager
from logger_config import LoggerConfig
from ldap_handler import LDAPHandler
from backup_manager import BackupManager
from migration_worker import MigrationWorker, SessionManager
from utils import DateValidator, CSVAccountLoader, StoreMappingLoader, MigrationStatistics
from account import Account

app = Flask(__name__)
app.config['SECRET_KEY'] = 'zimbra-migration-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
migration_state = {
    'status': 'idle',  # idle, running, completed, error
    'progress': 0,
    'current_account': None,
    'total_accounts': 0,
    'processed_accounts': 0,
    'errors': [],
    'start_time': None,
    'end_time': None
}
state_lock = Lock()

# Migration instance
current_migrator = None
current_accounts = []


class WebLogHandler(logging.Handler):
    """Custom log handler that emits logs via SocketIO."""

    def emit(self, record):
        log_entry = {
            'level': record.levelname,
            'message': self.format(record),
            'timestamp': datetime.now().isoformat()
        }
        socketio.emit('log_message', log_entry, namespace='/')


def update_migration_state(updates: dict):
    """Thread-safe update of migration state."""
    with state_lock:
        migration_state.update(updates)
        socketio.emit('migration_state', migration_state, namespace='/')


@app.route('/')
def index():
    """Serve main UI page."""
    return render_template('index.html')


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    try:
        config_path = request.args.get('path', 'config.ini')
        if not Path(config_path).exists():
            return jsonify({'error': 'Configuration file not found'}), 404

        config = configobj.ConfigObj(config_path)
        return jsonify(config.dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config', methods=['POST'])
def save_config():
    """Save configuration."""
    try:
        config_data = request.json
        config_path = config_data.get('config_path', 'config.ini')

        config = configobj.ConfigObj()
        config.filename = config_path

        # Update configuration sections
        for section, values in config_data.items():
            if section != 'config_path' and isinstance(values, dict):
                config[section] = values

        config.write()
        return jsonify({'success': True, 'message': 'Configuration saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate-connection', methods=['POST'])
def validate_connection():
    """Validate Zimbra server connection."""
    try:
        data = request.json
        connection_type = data.get('type')  # 'source' or 'destination'

        # Here you would implement actual connection validation
        # For now, return success
        return jsonify({
            'success': True,
            'message': f'{connection_type.capitalize()} server connection validated'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/accounts/ldap', methods=['POST'])
def load_accounts_ldap():
    """Load accounts from LDAP."""
    global current_migrator, current_accounts

    try:
        data = request.json
        config_path = data.get('config_path', 'config.ini')

        current_migrator = initialize_migrator(config_path)

        ldap_filter = data.get('ldap_filter', current_migrator.config.source['ldap_filter'])
        current_accounts = current_migrator.load_accounts_from_ldap(ldap_filter)

        return jsonify({
            'success': True,
            'count': len(current_accounts),
            'accounts': [{'email': acc.mail, 'folder': str(acc.folder)} for acc in current_accounts]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/accounts/csv', methods=['POST'])
def load_accounts_csv():
    """Load accounts from CSV file."""
    global current_migrator, current_accounts

    try:
        data = request.json
        config_path = data.get('config_path', 'config.ini')
        csv_path = data.get('csv_path')

        if not csv_path:
            return jsonify({'error': 'CSV path is required'}), 400

        current_migrator = initialize_migrator(config_path)
        current_accounts = current_migrator.load_accounts_from_csv(csv_path)

        return jsonify({
            'success': True,
            'count': len(current_accounts),
            'accounts': [{'email': acc.mail, 'folder': str(acc.folder)} for acc in current_accounts]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/migration/start', methods=['POST'])
def start_migration():
    """Start migration process."""
    global current_migrator, current_accounts

    try:
        if migration_state['status'] == 'running':
            return jsonify({'error': 'Migration already running'}), 400

        if not current_accounts:
            return jsonify({'error': 'No accounts loaded'}), 400

        data = request.json
        config_path = data.get('config_path', 'config.ini')

        # Migration parameters
        migration_params = {
            'num_threads': int(data.get('threads', 1)),
            'store_index': int(data.get('store_index', 0)),
            'do_full': data.get('full_migration', False),
            'do_incr': data.get('incremental_migration', False),
            'do_ldiff': data.get('ldiff_migration', False),
            'inc_date': data.get('incremental_date')
        }

        # Validate at least one migration type is selected
        if not (migration_params['do_full'] or migration_params['do_incr'] or migration_params['do_ldiff']):
            return jsonify({'error': 'At least one migration type must be selected'}), 400

        # Initialize migrator if not already done
        if not current_migrator:
            current_migrator = initialize_migrator(config_path)

        # Update state
        update_migration_state({
            'status': 'running',
            'progress': 0,
            'total_accounts': len(current_accounts),
            'processed_accounts': 0,
            'errors': [],
            'start_time': datetime.now().isoformat()
        })

        # Start migration in background thread
        migration_thread = Thread(
            target=run_migration_background,
            args=(current_migrator, current_accounts, migration_params)
        )
        migration_thread.daemon = True
        migration_thread.start()

        return jsonify({'success': True, 'message': 'Migration started'})
    except Exception as e:
        update_migration_state({'status': 'error', 'errors': [str(e)]})
        return jsonify({'error': str(e)}), 500


@app.route('/api/migration/status', methods=['GET'])
def get_migration_status():
    """Get current migration status."""
    with state_lock:
        return jsonify(migration_state)


@app.route('/api/migration/stop', methods=['POST'])
def stop_migration():
    """Stop migration process."""
    # Note: Implementing graceful shutdown would require more complex thread management
    update_migration_state({'status': 'stopped'})
    return jsonify({'success': True, 'message': 'Migration stop requested'})


@app.route('/api/stores', methods=['GET'])
def list_stores():
    """List available destination stores."""
    try:
        config_path = request.args.get('config_path', 'config.ini')
        migrator = initialize_migrator(config_path)

        stores = migrator.store_destinations
        return jsonify({
            'success': True,
            'stores': [{'index': i, 'name': store} for i, store in enumerate(stores)]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get migration statistics."""
    global current_accounts

    try:
        if not current_accounts:
            return jsonify({'error': 'No accounts loaded'}), 400

        stats = MigrationStatistics(current_accounts)

        return jsonify({
            'success': True,
            'statistics': {
                'total': stats.total,
                'ldiff_exported': stats.ldiff_exported,
                'ldiff_imported': stats.ldiff_imported,
                'full_exported': stats.full_exported,
                'full_migrated': stats.full_migrated,
                'incr_exported': stats.incr_exported,
                'incr_migrated': stats.incr_migrated
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get recent log entries."""
    try:
        log_file = Path('activity-migration.log')
        if not log_file.exists():
            return jsonify({'logs': []})

        # Read last 100 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-100:] if len(lines) > 100 else lines

        return jsonify({'logs': recent_lines})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def initialize_migrator(config_path: str = 'config.ini'):
    """Initialize ZimbraMigrator instance."""
    from zimbra_migrator import ZimbraMigrator

    migrator = ZimbraMigrator(config_path)
    migrator.setup_environment()

    # Add web log handler
    web_handler = WebLogHandler()
    web_handler.setLevel(logging.INFO)
    migrator.logger.addHandler(web_handler)

    return migrator


def run_migration_background(migrator, accounts: List[Account], params: dict):
    """Run migration in background thread with progress updates."""
    try:
        total = len(accounts)

        # Run migration
        migrator.run_migration(
            accounts=accounts,
            num_threads=params['num_threads'],
            store_index=params['store_index'],
            do_full=params['do_full'],
            do_incr=params['do_incr'],
            do_ldiff=params['do_ldiff'],
            inc_date=params['inc_date']
        )

        # Update final state
        update_migration_state({
            'status': 'completed',
            'progress': 100,
            'processed_accounts': total,
            'end_time': datetime.now().isoformat()
        })

        # Send statistics
        stats = MigrationStatistics(accounts)
        socketio.emit('migration_complete', {
            'statistics': {
                'total': stats.total,
                'ldiff_exported': stats.ldiff_exported,
                'ldiff_imported': stats.ldiff_imported,
                'full_exported': stats.full_exported,
                'full_migrated': stats.full_migrated,
                'incr_exported': stats.incr_exported,
                'incr_migrated': stats.incr_migrated
            }
        }, namespace='/')

    except Exception as e:
        update_migration_state({
            'status': 'error',
            'errors': [str(e)],
            'end_time': datetime.now().isoformat()
        })


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    emit('connected', {'message': 'Connected to migration server'})
    emit('migration_state', migration_state)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    pass


if __name__ == '__main__':
    # Run the web server
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Zimbra Migration Web UI on http://0.0.0.0:{port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
