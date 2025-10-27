#!/bin/bash
################################################################################
# ZCS Migration Post-Migration Verification Script
#
# This script verifies the success of the migration by comparing
# source and destination servers.
################################################################################

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/migration.conf"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓${NC} $*"
}

print_error() {
    echo -e "${RED}✗${NC} $*"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $*"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $*"
}

print_header() {
    echo ""
    echo "========================================"
    echo "$*"
    echo "========================================"
}

# Load configuration
if [[ ! -f "$CONFIG_FILE" ]]; then
    print_error "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# shellcheck disable=SC1090
source "$CONFIG_FILE"

# Compare counts
compare_counts() {
    local item=$1
    local source_count=$2
    local dest_count=$3
    
    if [[ $source_count -eq $dest_count ]]; then
        print_success "$item: $source_count (source) = $dest_count (destination)"
        return 0
    elif [[ $dest_count -ge $source_count ]]; then
        print_warning "$item: $source_count (source) < $dest_count (destination) - Extra items on destination"
        return 0
    else
        print_error "$item: $source_count (source) > $dest_count (destination) - Missing items!"
        return 1
    fi
}

# Verify domains
verify_domains() {
    print_header "Verifying Domains"
    
    local source_domains dest_domains
    
    source_domains=$(ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "su - zimbra -c 'zmprov gad'" 2>/dev/null | sort)
    dest_domains=$(ssh "$DEST_SSH_USER@$DEST_SERVER" "su - zimbra -c 'zmprov gad'" 2>/dev/null | sort)
    
    local source_count dest_count
    source_count=$(echo "$source_domains" | grep -v '^$' | wc -l)
    dest_count=$(echo "$dest_domains" | grep -v '^$' | wc -l)
    
    compare_counts "Domains" "$source_count" "$dest_count"
    
    # Check for missing domains
    print_info "Checking for missing domains..."
    local missing_domains
    missing_domains=$(comm -23 <(echo "$source_domains") <(echo "$dest_domains"))
    
    if [[ -z "$missing_domains" ]]; then
        print_success "All domains migrated successfully"
    else
        print_error "Missing domains on destination:"
        echo "$missing_domains" | while IFS= read -r domain; do
            [[ -z "$domain" ]] && continue
            echo "  - $domain"
        done
    fi
}

# Verify accounts
verify_accounts() {
    print_header "Verifying Accounts"
    
    local source_accounts dest_accounts
    
    print_info "Fetching account lists (this may take a moment)..."
    source_accounts=$(ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "su - zimbra -c 'zmprov -l gaa'" 2>/dev/null | sort)
    dest_accounts=$(ssh "$DEST_SSH_USER@$DEST_SERVER" "su - zimbra -c 'zmprov -l gaa'" 2>/dev/null | sort)
    
    local source_count dest_count
    source_count=$(echo "$source_accounts" | grep -v '^$' | wc -l)
    dest_count=$(echo "$dest_accounts" | grep -v '^$' | wc -l)
    
    compare_counts "Accounts" "$source_count" "$dest_count"
    
    # Check for missing accounts
    print_info "Checking for missing accounts..."
    local missing_accounts
    missing_accounts=$(comm -23 <(echo "$source_accounts") <(echo "$dest_accounts"))
    
    if [[ -z "$missing_accounts" ]]; then
        print_success "All accounts migrated successfully"
    else
        print_error "Missing accounts on destination:"
        echo "$missing_accounts" | head -20 | while IFS= read -r account; do
            [[ -z "$account" ]] && continue
            echo "  - $account"
        done
        
        local missing_count
        missing_count=$(echo "$missing_accounts" | grep -v '^$' | wc -l)
        if [[ $missing_count -gt 20 ]]; then
            print_warning "... and $((missing_count - 20)) more accounts"
        fi
    fi
}

# Verify distribution lists
verify_distribution_lists() {
    print_header "Verifying Distribution Lists"
    
    local source_dls dest_dls
    
    source_dls=$(ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "su - zimbra -c 'zmprov gadl'" 2>/dev/null | sort)
    dest_dls=$(ssh "$DEST_SSH_USER@$DEST_SERVER" "su - zimbra -c 'zmprov gadl'" 2>/dev/null | sort)
    
    local source_count dest_count
    source_count=$(echo "$source_dls" | grep -v '^$' | wc -l)
    dest_count=$(echo "$dest_dls" | grep -v '^$' | wc -l)
    
    compare_counts "Distribution Lists" "$source_count" "$dest_count"
    
    # Check for missing distribution lists
    print_info "Checking for missing distribution lists..."
    local missing_dls
    missing_dls=$(comm -23 <(echo "$source_dls") <(echo "$dest_dls"))
    
    if [[ -z "$missing_dls" ]]; then
        print_success "All distribution lists migrated successfully"
    else
        print_error "Missing distribution lists on destination:"
        echo "$missing_dls" | while IFS= read -r dl; do
            [[ -z "$dl" ]] && continue
            echo "  - $dl"
        done
    fi
}

# Sample account verification
verify_sample_account() {
    print_header "Sample Account Verification"
    
    print_info "Testing a sample account from destination server..."
    
    # Get first non-system account
    local sample_account
    sample_account=$(ssh "$DEST_SSH_USER@$DEST_SERVER" "su - zimbra -c 'zmprov -l gaa'" 2>/dev/null | grep -v "admin@" | grep -v "spam\." | grep -v "ham\." | grep -v "virus-quarantine\." | head -1)
    
    if [[ -z "$sample_account" ]]; then
        print_warning "No sample account found for testing"
        return 0
    fi
    
    print_info "Sample account: $sample_account"
    
    # Get account info
    local account_info
    account_info=$(ssh "$DEST_SSH_USER@$DEST_SERVER" "su - zimbra -c 'zmprov ga $sample_account'" 2>/dev/null)
    
    if [[ -n "$account_info" ]]; then
        print_success "Sample account exists and is accessible"
        
        # Extract some basic info
        local display_name status
        display_name=$(echo "$account_info" | grep "^displayName:" | cut -d: -f2- | sed 's/^ //' || echo "N/A")
        status=$(echo "$account_info" | grep "^zimbraAccountStatus:" | cut -d: -f2- | sed 's/^ //' || echo "N/A")
        
        print_info "  Display Name: $display_name"
        print_info "  Status: $status"
    else
        print_error "Could not retrieve sample account information"
    fi
}

# Check mailbox sizes
verify_mailbox_sizes() {
    print_header "Verifying Mailbox Sizes"
    
    print_info "Checking mailbox data sizes..."
    
    local source_size dest_size
    source_size=$(ssh "$SOURCE_SSH_USER@$SOURCE_SERVER" "du -sh /opt/zimbra/store 2>/dev/null | awk '{print \$1}'" 2>/dev/null || echo "unknown")
    dest_size=$(ssh "$DEST_SSH_USER@$DEST_SERVER" "du -sh /opt/zimbra/store 2>/dev/null | awk '{print \$1}'" 2>/dev/null || echo "unknown")
    
    print_info "Source mailbox size: $source_size"
    print_info "Destination mailbox size: $dest_size"
    
    if [[ "$source_size" != "unknown" ]] && [[ "$dest_size" != "unknown" ]]; then
        print_success "Mailbox data exists on both servers"
    else
        print_warning "Could not determine mailbox sizes"
    fi
}

# Check ZCS services
verify_services() {
    print_header "Verifying ZCS Services"
    
    print_info "Checking destination server services..."
    
    local services_status
    services_status=$(ssh "$DEST_SSH_USER@$DEST_SERVER" "su - zimbra -c 'zmcontrol status'" 2>/dev/null || echo "unknown")
    
    if [[ "$services_status" != "unknown" ]]; then
        local running_count
        running_count=$(echo "$services_status" | grep -c "Running" || echo "0")
        local stopped_count
        stopped_count=$(echo "$services_status" | grep -c "Stopped" || echo "0")
        
        print_info "Running services: $running_count"
        print_info "Stopped services: $stopped_count"
        
        if [[ $running_count -gt 0 ]] && [[ $stopped_count -eq 0 ]]; then
            print_success "All services are running on destination server"
        else
            print_warning "Some services are not running"
            print_info "Service status:"
            echo "$services_status" | grep -v "^Host" | while IFS= read -r line; do
                [[ -z "$line" ]] && continue
                echo "  $line"
            done
        fi
    else
        print_error "Could not check service status"
    fi
}

# Generate summary report
generate_summary() {
    print_header "Migration Verification Summary"
    
    echo ""
    echo "Source Server: $SOURCE_SERVER"
    echo "Destination Server: $DEST_SERVER"
    echo "Verification Date: $(date)"
    echo ""
    
    print_info "Migration verification completed"
    print_info "Review the results above for any issues"
    echo ""
    
    print_header "Next Steps"
    echo ""
    echo "1. Test user logins on destination server"
    echo "   - Try logging in with several test accounts"
    echo "   - Verify email access through web interface"
    echo ""
    echo "2. Test email delivery"
    echo "   - Send test emails to migrated accounts"
    echo "   - Verify internal and external delivery"
    echo ""
    echo "3. Update DNS records"
    echo "   - Point MX records to new server"
    echo "   - Update A/AAAA records as needed"
    echo ""
    echo "4. Monitor the system"
    echo "   - Watch logs for errors: /var/log/zimbra.log"
    echo "   - Monitor disk space usage"
    echo "   - Check service status regularly"
    echo ""
    echo "5. User communication"
    echo "   - Notify users about password changes"
    echo "   - Provide login instructions"
    echo "   - Set up support channels"
    echo ""
}

# Main execution
main() {
    print_header "ZCS Migration Post-Migration Verification"
    
    local errors=0
    
    verify_domains || ((errors++))
    verify_accounts || ((errors++))
    verify_distribution_lists || ((errors++))
    verify_sample_account || ((errors++))
    verify_mailbox_sizes || ((errors++))
    verify_services || ((errors++))
    
    generate_summary
    
    if [[ $errors -eq 0 ]]; then
        print_success "Verification completed successfully!"
        return 0
    else
        print_error "Verification completed with $errors issue(s)"
        print_warning "Please review and address the issues above"
        return 1
    fi
}

main "$@"
