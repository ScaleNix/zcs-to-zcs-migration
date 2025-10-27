# Testing Guide

This guide explains how to test the ZCS migration scripts in a safe environment.

## Test Environment Setup

### Requirements for Testing

1. **Two Test ZCS Servers**
   - Same ZCS version on both
   - Minimal test data
   - Not production systems

2. **Test Data**
   - 2-3 test domains
   - 10-20 test accounts
   - 1-2 distribution lists
   - Small amount of test email data

## Setting Up Test Environment

### Option 1: Virtual Machines

```bash
# Create two VMs with:
# - Ubuntu 20.04 or CentOS 7/8
# - 4GB RAM minimum
# - 40GB disk space
# - Network connectivity

# Install ZCS on both VMs (same version)
# Configure basic email setup
```

### Option 2: Docker Containers

```bash
# Use Zimbra Docker images
docker pull zimbra/zimbra-8
# Set up two containers with proper networking
```

## Test Scenarios

### Test 1: Pre-Flight Checks

**Purpose**: Verify environment validation

```bash
# Configure migration.conf with test servers
cp migration.conf.example migration.conf
# Edit with test server details

# Run pre-flight checks
./preflight-check.sh

# Expected results:
# - All checks should pass
# - SSH connections successful
# - Version match confirmed
# - Disk space adequate
```

### Test 2: Help and Documentation

**Purpose**: Verify user guidance

```bash
# Test help output
./migrate.sh --help

# Expected:
# - Shows usage information
# - No errors without config file
```

### Test 3: Export Only

**Purpose**: Test data export from source

```bash
# Run export only
./migrate.sh --export-only

# Verify:
# - migration_data/ directory created
# - domains.txt exists and contains domains
# - accounts.txt exists and contains accounts
# - distribution_lists.txt exists
# - No errors in logs
```

### Test 4: Import Only

**Purpose**: Test data import to destination

```bash
# After successful export
./migrate.sh --import-only

# Verify:
# - Domains created on destination
# - Accounts created on destination
# - Distribution lists created
# - Check logs for success messages
```

### Test 5: Full Migration

**Purpose**: Complete end-to-end test

```bash
# Clean slate: reset destination server
# Run full migration
./migrate.sh

# Verify:
# - Export phase completes
# - Import phase completes
# - Mailbox sync runs (even with minimal data)
# - No critical errors
```

### Test 6: Verification

**Purpose**: Test post-migration checks

```bash
./post-migration-verify.sh

# Expected:
# - Domain count matches
# - Account count matches
# - Distribution list count matches
# - Services running
```

### Test 7: Dry Run Mode

**Purpose**: Test without making changes

```bash
# Edit migration.conf:
# DRY_RUN=true

./migrate.sh

# Verify:
# - Shows what would be done
# - No actual changes made
# - Mailbox sync shows estimate only
```

## Validation Checklist

After each test, verify:

- [ ] Script executes without syntax errors
- [ ] Logs are created in logs/ directory
- [ ] Error messages are clear and helpful
- [ ] Success messages are displayed
- [ ] Data files are created correctly
- [ ] No sensitive data in logs

## Common Test Issues

### SSH Connection Fails

```bash
# Ensure SSH keys are set up
ssh-keygen -t rsa
ssh-copy-id root@test-source
ssh-copy-id root@test-dest
```

### Version Mismatch in Test

```bash
# Acceptable in test environment
# Set in migration.conf:
IGNORE_VERSION_MISMATCH=true
```

### Insufficient Test Data

```bash
# Create test data on source
ssh root@test-source
su - zimbra
zmprov cd testdomain.com
zmprov ca user1@testdomain.com password123
zmprov ca user2@testdomain.com password123
zmprov cdl testlist@testdomain.com
zmprov adlm testlist@testdomain.com user1@testdomain.com
```

## Performance Testing

### Small Dataset (< 1GB)

```bash
time ./migrate.sh
# Note execution time
# Should complete in minutes
```

### Medium Dataset (1-10GB)

```bash
# Monitor progress
./migrate.sh &
tail -f logs/migration_*.log
```

## Security Testing

### Check for Sensitive Data Leaks

```bash
# Review logs for passwords
grep -i "password" logs/migration_*.log

# Verify gitignore works
git status
# Should not show migration.conf or logs/
```

### Verify SSH Key Usage

```bash
# Ensure password-less authentication
ssh -o BatchMode=yes root@test-source echo "OK"
```

## Cleanup After Testing

```bash
# Remove test data
rm -rf migration_data/
rm -rf logs/

# Reset destination server
# Reinstall or restore from backup

# Remove test configuration
rm migration.conf
```

## Automated Testing (Future)

### Test Script Structure

```bash
#!/bin/bash
# test-suite.sh

test_preflight_checks() {
    ./preflight-check.sh
    assert_equals $? 0
}

test_export_creates_files() {
    ./migrate.sh --export-only
    assert_file_exists "migration_data/domains.txt"
    assert_file_exists "migration_data/accounts.txt"
}

# Run all tests
run_tests
```

## Reporting Test Results

When reporting issues, include:

1. Test scenario executed
2. Expected vs actual behavior
3. Log file excerpts
4. Environment details:
   - ZCS version
   - OS version
   - Script version
5. Steps to reproduce

## Continuous Testing

### Before Each Release

- [ ] Run all test scenarios
- [ ] Test on multiple OS versions
- [ ] Test with different ZCS versions
- [ ] Verify documentation accuracy
- [ ] Check for security issues

### Regular Testing

- [ ] Monthly: Full test suite
- [ ] After changes: Affected components
- [ ] Before updates: Regression testing

---

**Remember**: Always test in a non-production environment first!
