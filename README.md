# Zimbra to Zimbra Migration Tool

A modern, Python-based tool for migrating Zimbra Collaboration Suite (ZCS) accounts between servers with support for full backups, incremental migrations, and LDAP data transfer.

## Features

- **Full Migration**: Complete account data migration including emails, contacts, calendars, and settings
- **Incremental Migration**: Migrate only changes since a specific date
- **LDAP Support**: Export and import LDAP directory information (LDIFF)
- **Multi-threaded**: Parallel processing for faster migrations
- **Session Management**: Resume interrupted migrations without duplicating work
- **Load Balancing**: Distribute accounts across multiple destination stores
- **Comprehensive Logging**: Detailed logs for troubleshooting and audit trails
- **CSV Support**: Load accounts from CSV files or LDAP queries

## Architecture

The tool follows a modular object-oriented design with the following components:

- `zimbra_migrator.py` - Main orchestrator and CLI entry point
- `config_manager.py` - Configuration file handling
- `logger_config.py` - Centralized logging setup
- `account.py` - Account data model and folder management
- `backup_manager.py` - Backup/restore operations via curl and LDAP tools
- `migration_worker.py` - Multi-threaded migration workers
- `ldap_handler.py` - LDAP query and account loading
- `utils.py` - Utilities for CSV loading, date validation, and statistics

## Requirements

- Python 3.7+
- Zimbra Collaboration Suite (source and destination)
- LDAP access to Zimbra directory
- SSH access to Zimbra servers (for some operations)
- Administrative credentials for both source and destination servers

### Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `python-ldap>=3.4.0`
- `configobj>=5.0.8`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd zcs-to-zcs-migration
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create configuration file:
```bash
cp config.ini.example config.ini
```

4. Edit `config.ini` with your environment details (see Configuration section below)

## 📝 Configuration

### config.ini

```ini
[zimbra_source]
host = source.zimbra.com
admin_user = admin
admin_password = password
ldap_protocol = ldap://
ldap_host = ldap.source.com
ldap_port = 389
ldap_user = cn=zimbra,cn=admins,cn=zimbra
ldap_pass = password
ldap_base_dn = ou=people,dc=zimbra,dc=com
ldap_filter = (objectClass=zimbraAccount)

[zimbra_destination]
host = destination.zimbra.com
admin_user = admin
admin_password = password
ldap_host = ldap.destination.com
ldap_port = 389
ldap_user = cn=zimbra,cn=admins,cn=zimbra
ldap_pass = password
ldap_filter = (objectClass=zimbraAccount)

[global]
root_folder = /opt/zimbra/backup/
session_file = sessions.txt
log_level = INFO
```

### zimbra_mail_hosts.csv

```csv
user1@domain.com,mailstore1.zimbra.com
user2@domain.com,mailstore2.zimbra.com
```

## 🎮 Usage

### Basic Commands

**List available stores:**
```bash
./zimbra_migrator.py -b -t 1 -ldap
```

**Full migration from LDAP:**
```bash
./zimbra_migrator.py -ldap -f -l -t 4 -d 1
```

**Full migration from CSV:**
```bash
./zimbra_migrator.py -s accounts.csv -f -l -t 4 -d 1
```

**Incremental migration:**
```bash
./zimbra_migrator.py -ldap -i -at 01/15/2025 -t 4
```

**Automatic incremental (cron):**
```bash
./zimbra_migrator.py -ldap -i -at cron -t 4
```

### Command-Line Options

```
-ldap, --ldap                Load accounts from LDAP
-s, --source FILE            Load accounts from CSV file
-f, --full                   Perform full migration
-i, --incr                   Perform incremental migration
-l, --ldiff                  Perform LDIFF export/import
-t, --thread N               Number of threads to use
-d, --destination-store N    Destination store index (default: 1)
-at, --at-time DATE          Incremental date (MM/DD/YYYY) or "cron"
-b, --l-destination-store    List all destination stores
-c, --config FILE            Path to config file (default: config.ini)
```

## 🏗️ Architecture

### Class Diagram

```
┌─────────────────┐
│ ZimbraMigrator │ (Main Orchestrator)
└────────┬────────┘
         │
         ├── ConfigManager (Configuration)
         ├── LDAPHandler (LDAP Operations)
         ├── BackupManager (Backup/Restore)
         ├── SessionManager (Session Tracking)
         └── MigrationWorker (Threading)
                    │
                    └── Account (Data Model)
```

### Key Components

**ConfigManager**: Loads and validates configuration from INI file

**LDAPHandler**: Manages LDAP connections and queries for account discovery

**BackupManager**: Handles all backup and restore operations via curl

**MigrationWorker**: Thread worker for parallel processing

**SessionManager**: Thread-safe session tracking for resume capability

**Account**: Data model representing a user account with migration state

## 🔧 Improvements Over Original

1. **Modern Python 3**: Type hints, f-strings, pathlib
2. **Proper OOP**: Clear separation of concerns
3. **Better Error Handling**: Custom exceptions and proper logging
4. **No Deprecated Modules**: Replaced `commands` with `subprocess`
5. **Thread Safety**: Proper locking mechanisms
6. **Testability**: Modular design allows easy unit testing
7. **Maintainability**: Well-documented, following PEP 8
8. **Extensibility**: Easy to add new features

## 📊 Migration Statistics

After migration, the tool displays:

- Total accounts processed
- LDIFF exports/imports
- Full migrations completed
- Incremental migrations completed
- Detailed per-account status

## 🐛 Troubleshooting

**Check logs:**
```bash
tail -f activity-migration.log
```

**Per-account logs:**
```bash
ls /opt/zimbra/backup/user@domain.com/*.log
```

**Resume failed migration:**
The tool automatically tracks completed operations in `sessions.txt` and skips them on re-run.

## 📜 License

[Your License Here]

## 🤝 Contributing

Contributions are welcome! Please follow PEP 8 style guidelines and add tests for new features.

## ✨ Authors

- Original Script: [Original Author]
- Refactored by: ScaleNix Team (2025)