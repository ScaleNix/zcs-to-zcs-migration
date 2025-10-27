# Changelog

All notable changes to the ZCS to ZCS Migration project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-27

### Added
- Initial release of ZCS to ZCS migration script
- Core migration functionality:
  - Domain migration
  - Account migration with attributes
  - Distribution list migration
  - Mailbox data synchronization using rsync
- Pre-flight check script (`preflight-check.sh`)
  - SSH connectivity validation
  - ZCS version compatibility checking
  - Disk space verification
  - Service status checking
- Post-migration verification script (`post-migration-verify.sh`)
  - Domain, account, and distribution list verification
  - Sample account testing
  - Service status verification
- Configuration file system (`migration.conf.example`)
  - Flexible server configuration
  - Migration options
  - Security settings
- Comprehensive documentation:
  - Detailed README with usage instructions
  - Configuration guide
  - Best practices and troubleshooting
  - Contributing guidelines
- Logging system:
  - Timestamped log entries
  - Separate log files per migration run
  - Error, warning, and info levels
- Command-line options:
  - `--pre-checks`: Run only pre-migration checks
  - `--export-only`: Export data from source only
  - `--import-only`: Import data to destination only
  - `--verify`: Verify migration results
  - `--help`: Display usage information
- Security features:
  - Secure data directory handling
  - SSH key-based authentication support
  - Gitignore for sensitive files

### Features
- Automated domain export and import
- User account creation with display names and attributes
- Distribution list creation with member management
- Efficient mailbox data transfer using rsync
- Dry run capability for testing
- Version compatibility enforcement
- Comprehensive error handling
- Progress logging

### Documentation
- Complete README with:
  - Feature overview
  - Prerequisites and requirements
  - Installation instructions
  - Configuration guide
  - Usage examples
  - Migration strategy recommendations
  - Troubleshooting guide
- Example configuration file with detailed comments
- Contributing guidelines
- MIT License

### Security
- Gitignore for configuration files and sensitive data
- Secure directory creation
- SSH connection validation
- Password handling guidelines

## [Unreleased]

### Planned Features
- Parallel account migration for faster processing
- Resume capability for interrupted migrations
- Selective domain/account migration
- Email quota migration
- Calendar and contacts migration
- Zimlet migration support
- Email notification system
- Progress bars for long operations
- Backup creation before migration
- Rollback capability

### Planned Improvements
- Enhanced error recovery
- More detailed progress reporting
- Performance optimization
- Additional verification checks
- Support for external LDAP
- Multi-language support

---

## Version History

### Version 1.0.0 (2025-10-27)
First stable release with core migration functionality and comprehensive tooling.
