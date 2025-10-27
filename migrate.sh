#!/bin/bash
################################################################################
# ZCS to ZCS Migration Script
# 
# This script facilitates the migration of Zimbra Collaboration Suite (ZCS)
# from one server to another, including accounts, mailboxes, domains, and
# distribution lists.
#
# Usage: ./migrate.sh [options]
#
# Prerequisites:
# - Source and destination servers must have same ZCS version
# - SSH access to both servers
# - Sufficient disk space for data transfer
# - Configuration file (migration.conf) properly filled out
################################################################################

set -e  # Exit on error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to show usage (defined early to allow --help without config)
show_usage() {
    cat << EOF
ZCS to ZCS Migration Script

Usage: $0 [options]

Options:
    --pre-checks        Run only pre-migration checks
    --export-only       Export data from source only
    --import-only       Import data to destination only
    --verify            Verify migration only
    --help              Show this help message

Steps:
    1. Configure migration.conf with your server details
    2. Run with --pre-checks to validate setup
    3. Run without options to perform full migration
    4. Run with --verify to check migration results

EOF
}

# Check for --help before loading config
if [[ "${1:-}" == "--help" ]]; then
    show_usage
    exit 0
fi

set -u  # Exit on undefined variable (set after help check)

# Source configuration file
CONFIG_FILE="${SCRIPT_DIR}/migration.conf"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "ERROR: Configuration file not found: $CONFIG_FILE"
    echo "Please copy migration.conf.example to migration.conf and configure it."
    exit 1
fi

# shellcheck disable=SC1090
source "$CONFIG_FILE"

# Log directory
LOG_DIR="${LOG_DIR:-${SCRIPT_DIR}/logs}"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/migration_$(date +%Y%m%d_%H%M%S).log"

# Temporary directory for migration data
MIGRATION_DATA_DIR="${MIGRATION_DATA_DIR:-${SCRIPT_DIR}/migration_data}"
mkdir -p "$MIGRATION_DATA_DIR"

################################################################################
# Logging Functions
################################################################################

log_info() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $*"
    echo "$msg" | tee -a "$LOG_FILE"
}

log_error() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*"
    echo "$msg" | tee -a "$LOG_FILE" >&2
}

log_warning() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $*"
    echo "$msg" | tee -a "$LOG_FILE"
}

################################################################################
# Utility Functions
################################################################################

# Check if SSH connection is working
check_ssh_connection() {
    local server=$1
    local user=$2
    
    log_info "Checking SSH connection to $user@$server..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$user@$server" "echo 'SSH connection successful'" >/dev/null 2>&1; then
        log_info "SSH connection to $server successful"
        return 0
    else
        log_error "SSH connection to $server failed"
        return 1
    fi
}

# Get ZCS version from server
get_zcs_version() {
    local server=$1
    local user=$2
    
    ssh "$user@$server" "su - zimbra -c 'zmcontrol -v' 2>/dev/null | grep -oP 'Release \K[0-9.]+'" 2>/dev/null || echo "unknown"
}

# Check if ZCS versions match
check_version_compatibility() {
    log_info "Checking ZCS version compatibility..."
    
    local source_version
    local dest_version
    
    source_version=$(get_zcs_version "$SOURCE_SERVER" "$SOURCE_SSH_USER")
    dest_version=$(get_zcs_version "$DEST_SERVER" "$DEST_SSH_USER")
    
    log_info "Source ZCS version: $source_version"
    log_info "Destination ZCS version: $dest_version"
    
    if [[ "$source_version" != "$dest_version" ]]; then
        log_warning "ZCS versions do not match!"
        log_warning "Migration may encounter issues. Proceed with caution."
        if [[ "${IGNORE_VERSION_MISMATCH:-false}" != "true" ]]; then
            log_error "Set IGNORE_VERSION_MISMATCH=true in config to proceed anyway"
            return 1
        fi
    else
        log_info "ZCS versions match - proceeding with migration"
    fi
    
    return 0
}

################################################################################
# Pre-Migration Checks
################################################################################

pre_migration_checks() {
    log_info "=== Starting Pre-Migration Checks ==="
    
    # Check source server connection
    if ! check_ssh_connection "$SOURCE_SERVER" "$SOURCE_SSH_USER"; then
        log_error "Cannot connect to source server"
        return 1
    fi
    
    # Check destination server connection
    if ! check_ssh_connection "$DEST_SERVER" "$DEST_SSH_USER"; then
        log_error "Cannot connect to destination server"
        return 1
    fi
    
    # Check version compatibility
    if ! check_version_compatibility; then
        log_error "Version compatibility check failed"
        return 1
    fi
    
    # Check disk space on destination
    log_info "Checking disk space on destination server..."
    local dest_space
    dest_space=$(ssh "$DEST_SSH_USER@$DEST_SERVER" "df -BG /opt/zimbra | tail -1 | awk '{print \$4}' | sed 's/G//'")
    log_info "Available space on destination: ${dest_space}GB"
    
    if [[ $dest_space -lt 10 ]]; then
        log_warning "Low disk space on destination server: ${dest_space}GB"
    fi
    
    log_info "=== Pre-Migration Checks Completed ==="
    return 0
}

################################################################################
# Domain Migration
################################################################################

export_domains() {
    log_info "=== Exporting domains from source server ==="
    
    local domains_file="${MIGRATION_DATA_DIR}/domains.txt"
    
    ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "su - zimbra -c 'zmprov gad'" > "$domains_file"
    
    local domain_count
    domain_count=$(wc -l < "$domains_file")
    log_info "Exported $domain_count domains"
    
    return 0
}

import_domains() {
    log_info "=== Importing domains to destination server ==="
    
    local domains_file="${MIGRATION_DATA_DIR}/domains.txt"
    
    if [[ ! -f "$domains_file" ]]; then
        log_error "Domains file not found: $domains_file"
        return 1
    fi
    
    while IFS= read -r domain; do
        [[ -z "$domain" ]] && continue
        
        log_info "Creating domain: $domain"
        ssh "$DEST_SSH_USER@$DEST_SERVER" "su - zimbra -c 'zmprov cd $domain zimbraPublicServiceHostname $domain'" 2>&1 | tee -a "$LOG_FILE" || true
    done < "$domains_file"
    
    log_info "Domain import completed"
    return 0
}

################################################################################
# Account Migration
################################################################################

export_accounts() {
    log_info "=== Exporting accounts from source server ==="
    
    local accounts_file="${MIGRATION_DATA_DIR}/accounts.txt"
    
    # Export all accounts
    ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "su - zimbra -c 'zmprov -l gaa'" > "$accounts_file"
    
    local account_count
    account_count=$(wc -l < "$accounts_file")
    log_info "Exported $account_count accounts"
    
    # Export account details
    log_info "Exporting account details..."
    local accounts_detail_file="${MIGRATION_DATA_DIR}/accounts_detail.txt"
    > "$accounts_detail_file"
    
    while IFS= read -r account; do
        [[ -z "$account" ]] && continue
        
        log_info "Exporting details for: $account"
        ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "su - zimbra -c 'zmprov ga $account'" >> "$accounts_detail_file"
        echo "---" >> "$accounts_detail_file"
    done < "$accounts_file"
    
    log_info "Account export completed"
    return 0
}

import_accounts() {
    log_info "=== Importing accounts to destination server ==="
    
    local accounts_file="${MIGRATION_DATA_DIR}/accounts.txt"
    
    if [[ ! -f "$accounts_file" ]]; then
        log_error "Accounts file not found: $accounts_file"
        return 1
    fi
    
    while IFS= read -r account; do
        [[ -z "$account" ]] && continue
        
        # Skip system accounts
        if [[ "$account" == *"@"* ]] && [[ "$account" != "admin@"* ]] && [[ "$account" != "spam."* ]] && [[ "$account" != "ham."* ]] && [[ "$account" != "virus-quarantine."* ]]; then
            log_info "Creating account: $account"
            
            # Get account attributes from source
            local display_name
            local given_name
            local sn
            
            display_name=$(ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "su - zimbra -c 'zmprov ga $account displayName'" 2>/dev/null | grep "^displayName:" | cut -d: -f2- | sed 's/^ //' || echo "")
            given_name=$(ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "su - zimbra -c 'zmprov ga $account givenName'" 2>/dev/null | grep "^givenName:" | cut -d: -f2- | sed 's/^ //' || echo "")
            sn=$(ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "su - zimbra -c 'zmprov ga $account sn'" 2>/dev/null | grep "^sn:" | cut -d: -f2- | sed 's/^ //' || echo "")
            
            # Create account with default password
            local password="${DEFAULT_PASSWORD:-ChangeMe123!}"
            ssh "$DEST_SSH_USER@$DEST_SERVER" "su - zimbra -c 'zmprov ca $account $password displayName \"$display_name\" givenName \"$given_name\" sn \"$sn\"'" 2>&1 | tee -a "$LOG_FILE" || true
            
            log_info "Account created: $account"
        fi
    done < "$accounts_file"
    
    log_info "Account import completed"
    return 0
}

################################################################################
# Distribution List Migration
################################################################################

export_distribution_lists() {
    log_info "=== Exporting distribution lists from source server ==="
    
    local dl_file="${MIGRATION_DATA_DIR}/distribution_lists.txt"
    
    ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "su - zimbra -c 'zmprov gadl'" > "$dl_file"
    
    local dl_count
    dl_count=$(wc -l < "$dl_file")
    log_info "Exported $dl_count distribution lists"
    
    # Export distribution list members
    local dl_members_file="${MIGRATION_DATA_DIR}/dl_members.txt"
    > "$dl_members_file"
    
    while IFS= read -r dl; do
        [[ -z "$dl" ]] && continue
        
        log_info "Exporting members for DL: $dl"
        echo "DL: $dl" >> "$dl_members_file"
        ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "su - zimbra -c 'zmprov gdlm $dl'" >> "$dl_members_file" || true
        echo "---" >> "$dl_members_file"
    done < "$dl_file"
    
    log_info "Distribution list export completed"
    return 0
}

import_distribution_lists() {
    log_info "=== Importing distribution lists to destination server ==="
    
    local dl_file="${MIGRATION_DATA_DIR}/distribution_lists.txt"
    
    if [[ ! -f "$dl_file" ]]; then
        log_error "Distribution lists file not found: $dl_file"
        return 1
    fi
    
    while IFS= read -r dl; do
        [[ -z "$dl" ]] && continue
        
        log_info "Creating distribution list: $dl"
        ssh "$DEST_SSH_USER@$DEST_SERVER" "su - zimbra -c 'zmprov cdl $dl'" 2>&1 | tee -a "$LOG_FILE" || true
        
        # Add members
        log_info "Adding members to: $dl"
        local members
        members=$(ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "su - zimbra -c 'zmprov gdlm $dl'" 2>/dev/null || echo "")
        
        while IFS= read -r member; do
            [[ -z "$member" ]] && continue
            ssh "$DEST_SSH_USER@$DEST_SERVER" "su - zimbra -c 'zmprov adlm $dl $member'" 2>&1 | tee -a "$LOG_FILE" || true
        done <<< "$members"
        
    done < "$dl_file"
    
    log_info "Distribution list import completed"
    return 0
}

################################################################################
# Mailbox Data Sync
################################################################################

sync_mailbox_data() {
    log_info "=== Syncing mailbox data using rsync ==="
    
    if [[ "${SKIP_MAILBOX_SYNC:-false}" == "true" ]]; then
        log_warning "Skipping mailbox sync as per configuration"
        return 0
    fi
    
    local accounts_file="${MIGRATION_DATA_DIR}/accounts.txt"
    
    if [[ ! -f "$accounts_file" ]]; then
        log_error "Accounts file not found: $accounts_file"
        return 1
    fi
    
    log_info "Starting mailbox data synchronization..."
    log_info "This may take a considerable amount of time depending on data size"
    
    # Sync entire mailbox directory using rsync
    log_info "Syncing /opt/zimbra/store from source to destination..."
    
    # First do a dry run to estimate
    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        log_info "Performing dry run..."
        ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "rsync -avz --dry-run --progress --stats /opt/zimbra/store/ $DEST_SSH_USER@$DEST_SERVER:/opt/zimbra/store/" 2>&1 | tee -a "$LOG_FILE"
        log_info "Dry run completed. Review the output above."
        return 0
    fi
    
    # Actual sync
    log_info "Starting actual mailbox data sync..."
    ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "rsync -avz --progress /opt/zimbra/store/ $DEST_SSH_USER@$DEST_SERVER:/opt/zimbra/store/" 2>&1 | tee -a "$LOG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_info "Mailbox data sync completed successfully"
    else
        log_error "Mailbox data sync failed"
        return 1
    fi
    
    return 0
}

################################################################################
# Post-Migration Tasks
################################################################################

verify_migration() {
    log_info "=== Verifying migration ==="
    
    # Count accounts on destination
    log_info "Counting accounts on destination server..."
    local dest_account_count
    dest_account_count=$(ssh "$DEST_SSH_USER@$DEST_SERVER" "su - zimbra -c 'zmprov -l gaa | wc -l'")
    log_info "Destination server has $dest_account_count accounts"
    
    # Count domains on destination
    log_info "Counting domains on destination server..."
    local dest_domain_count
    dest_domain_count=$(ssh "$DEST_SSH_USER@$DEST_SERVER" "su - zimbra -c 'zmprov gad | wc -l'")
    log_info "Destination server has $dest_domain_count domains"
    
    # Count distribution lists on destination
    log_info "Counting distribution lists on destination server..."
    local dest_dl_count
    dest_dl_count=$(ssh "$DEST_SSH_USER@$DEST_SERVER" "su - zimbra -c 'zmprov gadl | wc -l'")
    log_info "Destination server has $dest_dl_count distribution lists"
    
    log_info "=== Migration verification completed ==="
    return 0
}

################################################################################
# Main Migration Process
################################################################################


main() {
    log_info "=== ZCS to ZCS Migration Started ==="
    log_info "Log file: $LOG_FILE"
    
    # Parse command line arguments
    local pre_checks_only=false
    local export_only=false
    local import_only=false
    local verify_only=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --pre-checks)
                pre_checks_only=true
                shift
                ;;
            --export-only)
                export_only=true
                shift
                ;;
            --import-only)
                import_only=true
                shift
                ;;
            --verify)
                verify_only=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Run pre-checks
    if ! pre_migration_checks; then
        log_error "Pre-migration checks failed"
        exit 1
    fi
    
    if [[ "$pre_checks_only" == "true" ]]; then
        log_info "Pre-checks completed successfully"
        exit 0
    fi
    
    # Verify only
    if [[ "$verify_only" == "true" ]]; then
        verify_migration
        exit 0
    fi
    
    # Export phase
    if [[ "$import_only" != "true" ]]; then
        export_domains || log_error "Domain export failed"
        export_accounts || log_error "Account export failed"
        export_distribution_lists || log_error "Distribution list export failed"
    fi
    
    if [[ "$export_only" == "true" ]]; then
        log_info "Export completed successfully"
        exit 0
    fi
    
    # Import phase
    if [[ "$export_only" != "true" ]]; then
        import_domains || log_error "Domain import failed"
        import_accounts || log_error "Account import failed"
        import_distribution_lists || log_error "Distribution list import failed"
        sync_mailbox_data || log_error "Mailbox sync failed"
    fi
    
    # Verify migration
    verify_migration
    
    log_info "=== ZCS to ZCS Migration Completed ==="
    log_info "Review the log file for details: $LOG_FILE"
    log_info ""
    log_info "Next steps:"
    log_info "1. Test user logins on destination server"
    log_info "2. Verify mail delivery"
    log_info "3. Update DNS records to point to new server"
    log_info "4. Monitor for any issues"
}

# Run main function
main "$@"
