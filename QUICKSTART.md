# Quick Start Guide

Get started with ZCS to ZCS migration in just a few steps.

## Prerequisites Checklist

- [ ] Both ZCS servers running same version
- [ ] SSH access to both servers (root or sudo)
- [ ] SSH key authentication configured
- [ ] Backup of both servers completed
- [ ] Maintenance window scheduled
- [ ] Users notified of migration

## 5-Minute Setup

### 1. Clone and Configure

```bash
# Clone the repository (or download the release)
git clone https://github.com/ScaleNix/zcs-to-zcs-migration.git
cd zcs-to-zcs-migration

# Create configuration file
cp migration.conf.example migration.conf

# Edit configuration with your server details
nano migration.conf
```

### 2. Configure Your Servers

Edit `migration.conf`:

```bash
SOURCE_SERVER="mail.oldserver.com"
SOURCE_SSH_USER="root"
DEST_SERVER="mail.newserver.com"
DEST_SSH_USER="root"
DEFAULT_PASSWORD="ChangeMe123!"
```

### 3. Run Pre-Flight Checks

```bash
./preflight-check.sh
```

This validates:
- SSH connectivity
- ZCS version compatibility
- Disk space
- Service status

### 4. Test the Migration (Optional)

```bash
# Set dry run mode
# Edit migration.conf: DRY_RUN=true

# Run migration in dry-run mode
./migrate.sh
```

### 5. Perform the Migration

```bash
# Full migration
./migrate.sh

# OR migrate in phases:

# Phase 1: Export from source
./migrate.sh --export-only

# Phase 2: Import to destination
./migrate.sh --import-only

# Phase 3: Verify
./migrate.sh --verify
```

### 6. Verify Migration

```bash
./post-migration-verify.sh
```

## Common Commands

### Check Script Help
```bash
./migrate.sh --help
```

### Pre-Migration Check Only
```bash
./migrate.sh --pre-checks
```

### Export Data Only
```bash
./migrate.sh --export-only
```

### Import Data Only
```bash
./migrate.sh --import-only
```

### Verify Migration
```bash
./migrate.sh --verify
```

## Migration Strategy

### For Small Installations (< 100 users)

1. Schedule 2-hour maintenance window
2. Run pre-flight checks
3. Stop source ZCS
4. Run full migration: `./migrate.sh`
5. Verify results
6. Update DNS
7. Start destination ZCS

### For Medium Installations (100-1000 users)

1. Schedule 4-6 hour maintenance window
2. Pre-sync data days before (reduces downtime):
   ```bash
   ./migrate.sh --export-only
   # Initial rsync of mailbox data
   ```
3. During maintenance:
   - Stop source ZCS
   - Run final sync: `./migrate.sh`
   - Verify results
   - Update DNS

### For Large Installations (> 1000 users)

1. Plan multi-day migration
2. Multiple pre-sync runs
3. Migrate in phases:
   - Day 1: Export and pre-sync (source still running)
   - Day 2-N: Additional incremental syncs
   - Final day: Stop source, final sync, verify, cutover

## Troubleshooting Quick Tips

### SSH Connection Failed
```bash
# Test manual SSH
ssh root@mail.oldserver.com

# If password prompted, set up SSH keys
ssh-copy-id root@mail.oldserver.com
```

### Version Mismatch
```bash
# Check versions on both servers
ssh root@source "zmcontrol -v"
ssh root@dest "zmcontrol -v"

# Either upgrade/downgrade or set IGNORE_VERSION_MISMATCH=true
```

### Insufficient Disk Space
```bash
# Check space
ssh root@dest "df -h /opt/zimbra"

# Clean up if needed
ssh root@dest "zimbra -c 'zmlocalconfig -e zimbraMailPurgeUseChangeDateForTrash=TRUE'"
```

### Migration Fails
```bash
# Check logs
tail -f logs/migration_*.log

# Retry specific phase
./migrate.sh --import-only
```

## Post-Migration Checklist

- [ ] All domains migrated
- [ ] All accounts created
- [ ] Distribution lists working
- [ ] Test user logins (web and client)
- [ ] Send test emails (internal/external)
- [ ] Verify mailbox data
- [ ] Update DNS records
- [ ] Monitor logs for errors
- [ ] Inform users of password change
- [ ] Document any issues

## Getting Help

- Check the full README.md for detailed information
- Review logs in `logs/` directory
- Search Zimbra forums for specific errors
- Open an issue on GitHub for bugs

## Important Notes

⚠️ **Always backup before migration**
⚠️ **Test in non-production environment first**
⚠️ **Monitor the migration process**
⚠️ **Keep source server until verification complete**

---

**Ready to migrate?** Start with `./preflight-check.sh`!
