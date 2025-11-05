# Quick Start Guide - Zimbra Migration Tool Web UI

This guide will help you get started with the Zimbra Migration Tool Web UI in just a few minutes.

## Prerequisites

- Python 3.7 or higher
- Access to source and destination Zimbra servers
- LDAP credentials for both servers
- Network connectivity to both Zimbra servers

## Step 1: Installation

### Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd zcs-to-zcs-migration

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configuration

### Create Configuration File

```bash
# Copy example config
cp config.ini.example config.ini

# Edit with your details
nano config.ini  # or use your preferred editor
```

### Configure Your Servers

Edit `config.ini` and update:

1. **Source Server Section** (`[zimbra_source]`):
   - `host` - Source Zimbra hostname
   - `admin_user` and `admin_password` - Admin credentials
   - LDAP connection details

2. **Destination Server Section** (`[zimbra_destination]`):
   - `host` - Destination Zimbra hostname
   - `admin_user` and `admin_password` - Admin credentials
   - LDAP connection details

3. **Global Settings** (`[global]`):
   - `root_folder` - Where to store backups
   - `log_level` - Logging verbosity (INFO recommended)

## Step 3: Start the Web UI

### Linux/Mac

```bash
./start_web_ui.sh
```

### Windows

```cmd
start_web_ui.bat
```

The web interface will start on: **http://localhost:5000**

## Step 4: Use the Web Interface

### 4.1 Verify Configuration

1. Open your browser to http://localhost:5000
2. Navigate to the **Configuration** section
3. Verify your server settings
4. Use "Validate Connection" buttons to test connectivity
5. Click "Save Configuration" if you made changes

### 4.2 Load Accounts

1. Navigate to **Load Accounts** section
2. Choose your method:
   - **From LDAP**: Enter optional filter or leave empty to use config default
   - **From CSV**: Enter path to CSV file (format: email,mailhost)
3. Click the load button
4. Review the loaded accounts in the table

### 4.3 Configure Migration

1. Navigate to **Migration** section
2. Select migration types:
   - ☑️ **Full Migration** - Complete account data
   - ☑️ **Incremental Migration** - Changes since a date
   - ☑️ **LDIFF Migration** - LDAP data export/import
3. Set parameters:
   - **Threads**: Number of parallel workers (4 recommended)
   - **Store Index**: Destination store (0 for first store)
   - **Incremental Date**: Only if incremental is selected (MM/DD/YYYY)

### 4.4 Start and Monitor Migration

1. Click **Start Migration**
2. Navigate to **Monitoring** section to watch progress
3. View real-time updates:
   - Progress bar
   - Current account being processed
   - Statistics
   - Any errors
4. Check **Logs** section for detailed information

## Step 5: Review Results

After migration completes:

1. Check the **Monitoring** section for:
   - Total accounts processed
   - Success/failure counts
   - Migration statistics

2. Review logs in **Logs** section for any issues

3. Verify accounts on destination server

## Common Use Cases

### Full Migration

For migrating all account data:

1. Load accounts from LDAP or CSV
2. Select "Full Migration" only
3. Set threads (e.g., 4)
4. Start migration

### Incremental Migration

For syncing recent changes:

1. Load accounts
2. Select "Incremental Migration"
3. Enter date (MM/DD/YYYY) or "cron" for auto
4. Start migration

### LDAP + Full Migration

For complete migration with LDAP data:

1. Load accounts
2. Select both "LDIFF Migration" and "Full Migration"
3. Configure threads and store
4. Start migration

## Troubleshooting

### Can't Connect to Web UI

- Check if port 5000 is available
- Set different port: `PORT=8080 ./start_web_ui.sh`
- Check firewall settings

### Connection Validation Fails

- Verify server hostnames are accessible
- Check admin credentials
- Verify LDAP settings
- Test network connectivity

### Accounts Not Loading

- Verify LDAP filter syntax
- Check LDAP credentials
- Review logs for specific errors
- Try loading from CSV instead

### Migration Errors

- Check logs in the Logs section
- Verify destination server has enough space
- Check session file for resume capability
- Review account-specific logs in backup folder

## Advanced Features

### Multiple Threads

For faster migration, increase thread count:
- Small migrations: 1-2 threads
- Medium migrations: 4-6 threads
- Large migrations: 8-10 threads

### Resume Failed Migrations

The tool automatically tracks completed operations in `sessions.txt`. Simply restart the migration - completed items will be skipped.

### CSV Format

For CSV account loading, use this format:

```csv
user1@domain.com,mailstore1.zimbra.com
user2@domain.com,mailstore2.zimbra.com
user3@domain.com,mailstore1.zimbra.com
```

## Security Notes

1. **Passwords**: Store `config.ini` securely - it contains admin passwords
2. **Network**: Use secure connections to Zimbra servers when possible
3. **LDAPS**: Consider using LDAPS (ldaps://) instead of LDAP
4. **Firewall**: Restrict access to Web UI port in production

## Getting Help

- Check the main README.md for detailed documentation
- Review logs for specific error messages
- Check Zimbra server logs for server-side issues
- Verify network connectivity and credentials

## Next Steps

After successful migration:

1. Verify all accounts on destination server
2. Test user logins
3. Check mailbox data integrity
4. Update DNS/MX records (when ready)
5. Monitor destination server performance

Happy migrating! 🚀
