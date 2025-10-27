# ZCS to ZCS Migration Script

A comprehensive Bash script for migrating Zimbra Collaboration Suite (ZCS) from one server to another. This tool automates the migration of domains, accounts, distribution lists, and mailbox data between ZCS servers.

## Features

- ✅ **Version Compatibility Check**: Ensures source and destination servers run compatible ZCS versions
- ✅ **Domain Migration**: Exports and imports all domains
- ✅ **Account Migration**: Migrates user accounts with attributes
- ✅ **Distribution Lists**: Transfers distribution lists and their members
- ✅ **Mailbox Data Sync**: Uses rsync for efficient data transfer
- ✅ **Pre-Migration Checks**: Validates SSH connectivity and system requirements
- ✅ **Post-Migration Verification**: Verifies successful migration
- ✅ **Comprehensive Logging**: Detailed logs for troubleshooting
- ✅ **Flexible Execution**: Support for partial migrations and dry runs

## Prerequisites

### Server Requirements

1. **Same ZCS Version**: Both source and destination servers must run the same ZCS version
2. **SSH Access**: Root or sudo SSH access to both servers
3. **SSH Key Authentication**: Password-less SSH between servers (recommended)
4. **Sufficient Disk Space**: Destination server needs adequate space for all mailbox data
5. **Network Connectivity**: Stable network connection between servers

### Before You Begin

- Backup both source and destination servers
- Test in a non-production environment first
- Plan for an appropriate maintenance window
- Notify users about the migration schedule
- Lower DNS TTL values 24-48 hours before migration

## Installation

1. Clone this repository:
```bash
git clone https://github.com/ScaleNix/zcs-to-zcs-migration.git
cd zcs-to-zcs-migration
```

2. Make the script executable:
```bash
chmod +x migrate.sh
```

3. Create and configure the migration settings:
```bash
cp migration.conf.example migration.conf
nano migration.conf  # or use your preferred editor
```

## Configuration

Edit `migration.conf` and set the following parameters:

```bash
# Source Server
SOURCE_SERVER="source.example.com"
SOURCE_SSH_USER="root"

# Destination Server
DEST_SERVER="destination.example.com"
DEST_SSH_USER="root"

# Migration Settings
DEFAULT_PASSWORD="ChangeMe123!"
IGNORE_VERSION_MISMATCH=false
SKIP_MAILBOX_SYNC=false
DRY_RUN=false
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `SOURCE_SERVER` | Hostname or IP of source ZCS server | Required |
| `SOURCE_SSH_USER` | SSH user for source server | `root` |
| `DEST_SERVER` | Hostname or IP of destination ZCS server | Required |
| `DEST_SSH_USER` | SSH user for destination server | `root` |
| `DEFAULT_PASSWORD` | Default password for migrated accounts | `ChangeMe123!` |
| `IGNORE_VERSION_MISMATCH` | Proceed even if versions don't match | `false` |
| `SKIP_MAILBOX_SYNC` | Skip mailbox data synchronization | `false` |
| `DRY_RUN` | Perform dry run without actual changes | `false` |
| `LOG_DIR` | Directory for log files | `./logs` |
| `MIGRATION_DATA_DIR` | Directory for migration data | `./migration_data` |

## Usage

### Basic Usage

Run the complete migration:
```bash
./migrate.sh
```

### Advanced Options

**Pre-migration checks only:**
```bash
./migrate.sh --pre-checks
```

**Export data from source only:**
```bash
./migrate.sh --export-only
```

**Import data to destination only:**
```bash
./migrate.sh --import-only
```

**Verify migration results:**
```bash
./migrate.sh --verify
```

**Show help:**
```bash
./migrate.sh --help
```

## Migration Process

The script follows this workflow:

1. **Pre-Migration Checks**
   - Validates SSH connectivity to both servers
   - Checks ZCS version compatibility
   - Verifies available disk space

2. **Export Phase**
   - Exports domains from source server
   - Exports user accounts and attributes
   - Exports distribution lists and members

3. **Import Phase**
   - Creates domains on destination server
   - Creates user accounts with default passwords
   - Creates distribution lists and adds members

4. **Data Synchronization**
   - Syncs mailbox data using rsync
   - Preserves email data, folders, and attachments

5. **Verification**
   - Counts and compares domains, accounts, and distribution lists
   - Generates summary report

## Migration Strategy

### Recommended Approach

1. **Initial Setup**
   ```bash
   # Run pre-checks
   ./migrate.sh --pre-checks
   ```

2. **Test Run** (Optional but recommended)
   ```bash
   # Set DRY_RUN=true in migration.conf
   ./migrate.sh
   ```

3. **Pre-sync** (Reduces final downtime)
   ```bash
   # Export data first
   ./migrate.sh --export-only
   
   # Do initial mailbox sync (can be run multiple times)
   # This syncs data while source is still running
   ```

4. **Final Migration**
   ```bash
   # Stop source ZCS (to prevent new data)
   # Run complete migration
   ./migrate.sh
   
   # Verify results
   ./migrate.sh --verify
   ```

5. **Post-Migration**
   - Test user logins on destination
   - Verify email delivery
   - Update DNS records
   - Monitor for issues

## Logging

Logs are stored in the `logs/` directory with timestamps:
```
logs/migration_20231027_143022.log
```

Each log entry includes:
- Timestamp
- Severity level (INFO, WARNING, ERROR)
- Detailed message

## Troubleshooting

### Common Issues

**SSH Connection Failed**
- Verify SSH key authentication is configured
- Check firewall rules between servers
- Test manual SSH connection: `ssh user@server`

**Version Mismatch**
- Ensure both servers run the same ZCS version
- Upgrade/downgrade if necessary
- Or set `IGNORE_VERSION_MISMATCH=true` (not recommended)

**Insufficient Disk Space**
- Check available space: `df -h /opt/zimbra`
- Clean up unnecessary files
- Consider external storage for temporary data

**Rsync Fails**
- Verify network connectivity
- Check rsync is installed on both servers
- Review rsync logs in the main log file

**Accounts Not Created**
- Check destination server LDAP is running
- Verify domain exists before creating accounts
- Review log file for specific errors

## Security Considerations

- **Never use /tmp** for migration data (use secure directories)
- **SSH Keys**: Use dedicated SSH keys for migration
- **Passwords**: Change default passwords immediately after migration
- **Logs**: Protect log files as they may contain sensitive information
- **Screen/Tmux**: Use session managers for remote operations

## Best Practices

1. **Backup Everything**: Full backup of both servers before migration
2. **Test First**: Run complete test migration in lab environment
3. **Incremental Sync**: Run rsync multiple times to reduce final downtime
4. **Monitor Progress**: Watch logs during migration
5. **Verify Thoroughly**: Test critical accounts and mail flow
6. **Documentation**: Document any custom configurations or changes
7. **Communication**: Keep users informed throughout the process

## Limitations

- Both servers must run the same ZCS version
- Migration does not include:
  - Admin console customizations
  - Zimlet configurations
  - Custom themes
  - SSL certificates
  - Some advanced server configurations

These items should be migrated manually or using ZCS-specific tools.

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/ScaleNix/zcs-to-zcs-migration/issues
- Zimbra Forums: https://forums.zimbra.org
- Zimbra Documentation: https://wiki.zimbra.com

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is provided as-is for use in ZCS migrations. Please review and test thoroughly before using in production environments.

## Acknowledgments

Based on best practices from:
- Zimbra Official Documentation
- Zimbra Community Forums
- Real-world migration experiences

## Version History

- **1.0.0** - Initial release
  - Complete migration workflow
  - Domain, account, and distribution list migration
  - Mailbox data sync with rsync
  - Comprehensive logging and error handling

## References

- [Zimbra Wiki - ZCS to ZCS Migration](https://wiki.zimbra.com/wiki/ZCS_to_ZCS_rsync_Migration)
- [Zimbra Tech Center](https://wiki.zimbra.com)
- [Zimbra Forums](https://forums.zimbra.org)