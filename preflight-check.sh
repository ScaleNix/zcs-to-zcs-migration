#!/bin/bash
################################################################################
# ZCS Migration Pre-Flight Check Script
#
# This script performs comprehensive pre-migration checks to ensure
# the environment is ready for migration.
################################################################################

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/migration.conf"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
    echo -e "ℹ $*"
}

# Check if configuration file exists
check_config_file() {
    echo "Checking configuration file..."
    if [[ -f "$CONFIG_FILE" ]]; then
        print_success "Configuration file found: $CONFIG_FILE"
        # shellcheck disable=SC1090
        source "$CONFIG_FILE"
        return 0
    else
        print_error "Configuration file not found: $CONFIG_FILE"
        print_info "Please copy migration.conf.example to migration.conf and configure it"
        return 1
    fi
}

# Check SSH connectivity
check_ssh() {
    local server=$1
    local user=$2
    local name=$3
    
    echo "Checking SSH connection to $name ($server)..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$user@$server" "echo 'SSH OK'" >/dev/null 2>&1; then
        print_success "SSH connection to $name successful"
        return 0
    else
        print_error "SSH connection to $name failed"
        print_info "Ensure SSH key-based authentication is configured"
        print_info "Test with: ssh $user@$server"
        return 1
    fi
}

# Check if ZCS is installed
check_zcs_installed() {
    local server=$1
    local user=$2
    local name=$3
    
    echo "Checking if ZCS is installed on $name..."
    if ssh "$user@$server" "test -d /opt/zimbra && echo 'ZCS installed'" >/dev/null 2>&1; then
        print_success "ZCS is installed on $name"
        return 0
    else
        print_error "ZCS is not installed on $name"
        return 1
    fi
}

# Check ZCS version
check_zcs_version() {
    local server=$1
    local user=$2
    local name=$3
    
    echo "Checking ZCS version on $name..."
    local version
    version=$(ssh "$user@$server" "su - zimbra -c 'zmcontrol -v' 2>/dev/null | grep -oP 'Release \K[0-9.]+'" 2>/dev/null || echo "unknown")
    
    if [[ "$version" != "unknown" ]]; then
        print_success "ZCS version on $name: $version"
        echo "$version"
        return 0
    else
        print_error "Could not determine ZCS version on $name"
        return 1
    fi
}

# Check ZCS service status
check_zcs_status() {
    local server=$1
    local user=$2
    local name=$3
    
    echo "Checking ZCS service status on $name..."
    local status
    status=$(ssh "$user@$server" "su - zimbra -c 'zmcontrol status'" 2>/dev/null | grep -c "Running" || echo "0")
    
    if [[ $status -gt 0 ]]; then
        print_success "ZCS services are running on $name"
        return 0
    else
        print_warning "Some ZCS services may not be running on $name"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    local server=$1
    local user=$2
    local name=$3
    
    echo "Checking disk space on $name..."
    local total_space available_space used_percentage
    
    disk_info=$(ssh "$user@$server" "df -BG /opt/zimbra | tail -1" 2>/dev/null)
    total_space=$(echo "$disk_info" | awk '{print $2}' | sed 's/G//')
    available_space=$(echo "$disk_info" | awk '{print $4}' | sed 's/G//')
    used_percentage=$(echo "$disk_info" | awk '{print $5}' | sed 's/%//')
    
    print_info "Total: ${total_space}GB, Available: ${available_space}GB, Used: ${used_percentage}%"
    
    if [[ $available_space -gt 50 ]]; then
        print_success "Sufficient disk space available on $name"
        return 0
    elif [[ $available_space -gt 20 ]]; then
        print_warning "Low disk space on $name: ${available_space}GB available"
        return 0
    else
        print_error "Insufficient disk space on $name: ${available_space}GB available"
        return 1
    fi
}

# Check network connectivity
check_network() {
    local server=$1
    local user=$2
    local name=$3
    
    echo "Checking network latency to $name..."
    local latency
    latency=$(ssh "$user@$server" "ping -c 3 $DEST_SERVER 2>/dev/null | tail -1 | grep -oP 'avg = \K[0-9.]+' || echo 'unknown'" 2>/dev/null)
    
    if [[ "$latency" != "unknown" ]]; then
        print_success "Network latency to destination: ${latency}ms"
        return 0
    else
        print_warning "Could not determine network latency"
        return 0
    fi
}

# Check rsync availability
check_rsync() {
    local server=$1
    local user=$2
    local name=$3
    
    echo "Checking if rsync is available on $name..."
    if ssh "$user@$server" "which rsync >/dev/null 2>&1"; then
        print_success "rsync is available on $name"
        return 0
    else
        print_error "rsync is not installed on $name"
        print_info "Install with: apt-get install rsync (Debian/Ubuntu) or yum install rsync (RHEL/CentOS)"
        return 1
    fi
}

# Check if required directories are writable
check_directories() {
    echo "Checking local directories..."
    
    local dirs=("logs" "migration_data")
    for dir in "${dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            print_success "Directory exists: $dir"
        else
            mkdir -p "$dir"
            print_success "Created directory: $dir"
        fi
        
        if [[ -w "$dir" ]]; then
            print_success "Directory writable: $dir"
        else
            print_error "Directory not writable: $dir"
            return 1
        fi
    done
    
    return 0
}

# Main execution
main() {
    echo "========================================"
    echo "ZCS Migration Pre-Flight Check"
    echo "========================================"
    echo ""
    
    local errors=0
    
    # Check configuration
    if ! check_config_file; then
        ((errors++))
        return 1
    fi
    
    echo ""
    echo "--- Local Environment Checks ---"
    check_directories || ((errors++))
    
    echo ""
    echo "--- Source Server Checks ($SOURCE_SERVER) ---"
    check_ssh "$SOURCE_SERVER" "$SOURCE_SSH_USER" "source server" || ((errors++))
    check_zcs_installed "$SOURCE_SERVER" "$SOURCE_SSH_USER" "source server" || ((errors++))
    source_version=$(check_zcs_version "$SOURCE_SERVER" "$SOURCE_SSH_USER" "source server") || ((errors++))
    check_zcs_status "$SOURCE_SERVER" "$SOURCE_SSH_USER" "source server" || ((errors++))
    check_disk_space "$SOURCE_SERVER" "$SOURCE_SSH_USER" "source server" || ((errors++))
    check_rsync "$SOURCE_SERVER" "$SOURCE_SSH_USER" "source server" || ((errors++))
    
    echo ""
    echo "--- Destination Server Checks ($DEST_SERVER) ---"
    check_ssh "$DEST_SERVER" "$DEST_SSH_USER" "destination server" || ((errors++))
    check_zcs_installed "$DEST_SERVER" "$DEST_SSH_USER" "destination server" || ((errors++))
    dest_version=$(check_zcs_version "$DEST_SERVER" "$DEST_SSH_USER" "destination server") || ((errors++))
    check_zcs_status "$DEST_SERVER" "$DEST_SSH_USER" "destination server" || ((errors++))
    check_disk_space "$DEST_SERVER" "$DEST_SSH_USER" "destination server" || ((errors++))
    check_rsync "$DEST_SERVER" "$DEST_SSH_USER" "destination server" || ((errors++))
    check_network "$SOURCE_SERVER" "$SOURCE_SSH_USER" "source server"
    
    echo ""
    echo "--- Version Compatibility Check ---"
    if [[ "$source_version" != "unknown" ]] && [[ "$dest_version" != "unknown" ]]; then
        if [[ "$source_version" == "$dest_version" ]]; then
            print_success "ZCS versions match: $source_version"
        else
            print_error "ZCS version mismatch!"
            print_info "Source: $source_version"
            print_info "Destination: $dest_version"
            print_warning "Set IGNORE_VERSION_MISMATCH=true in config to proceed (not recommended)"
            ((errors++))
        fi
    fi
    
    echo ""
    echo "========================================"
    if [[ $errors -eq 0 ]]; then
        print_success "All pre-flight checks passed!"
        echo ""
        echo "You are ready to proceed with the migration."
        echo "Run: ./migrate.sh"
    else
        print_error "Pre-flight checks failed with $errors error(s)"
        echo ""
        echo "Please resolve the errors above before proceeding."
        return 1
    fi
    echo "========================================"
}

main "$@"
