#!/bin/bash
################################################################################
# Example Migration Workflow
#
# This script demonstrates the recommended workflow for ZCS migration.
# Adapt this to your specific needs.
################################################################################

echo "========================================"
echo "ZCS Migration Example Workflow"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}==>${NC} $*"
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

# Step 1: Configuration check
print_step "Step 1: Configuration Check"
if [[ ! -f "migration.conf" ]]; then
    print_warning "Configuration file not found!"
    echo "Creating from example..."
    cp migration.conf.example migration.conf
    echo ""
    echo "Please edit migration.conf with your server details:"
    echo "  - SOURCE_SERVER"
    echo "  - DEST_SERVER"
    echo "  - SSH credentials"
    echo ""
    echo "After configuration, run this script again."
    exit 0
else
    print_info "Configuration file found"
fi

echo ""
read -p "Press Enter to continue to pre-flight checks..."

# Step 2: Pre-flight checks
print_step "Step 2: Running Pre-flight Checks"
echo ""
./preflight-check.sh

if [[ $? -ne 0 ]]; then
    print_warning "Pre-flight checks failed. Please fix the issues above."
    exit 1
fi

echo ""
read -p "Pre-flight checks passed. Continue to export phase? (y/n): " answer
if [[ "$answer" != "y" ]]; then
    echo "Exiting. Run again when ready."
    exit 0
fi

# Step 3: Export phase
print_step "Step 3: Exporting Data from Source Server"
echo ""
print_info "This will export domains, accounts, and distribution lists"
print_info "Mailbox sync will happen in the next phase"
echo ""
read -p "Continue with export? (y/n): " answer
if [[ "$answer" != "y" ]]; then
    echo "Export cancelled."
    exit 0
fi

./migrate.sh --export-only

if [[ $? -ne 0 ]]; then
    print_warning "Export failed. Check logs and retry."
    exit 1
fi

print_info "Export completed successfully"
echo ""
read -p "Press Enter to continue to import phase..."

# Step 4: Import and sync phase
print_step "Step 4: Importing Data to Destination Server"
echo ""
print_warning "IMPORTANT: This will modify the destination server!"
print_warning "Ensure you have backed up the destination server."
echo ""
read -p "Continue with import and sync? (y/n): " answer
if [[ "$answer" != "y" ]]; then
    echo "Import cancelled."
    exit 0
fi

print_info "Starting import phase..."
print_info "This may take considerable time depending on mailbox data size"
echo ""

./migrate.sh --import-only

if [[ $? -ne 0 ]]; then
    print_warning "Import failed. Check logs for details."
    exit 1
fi

print_info "Import completed successfully"
echo ""
read -p "Press Enter to verify migration..."

# Step 5: Verification
print_step "Step 5: Verifying Migration"
echo ""

./post-migration-verify.sh

echo ""
print_step "Migration Workflow Complete!"
echo ""
echo "Next steps:"
echo "1. Test user logins on destination server"
echo "2. Verify email delivery"
echo "3. Test several user accounts thoroughly"
echo "4. Update DNS records when ready"
echo "5. Monitor destination server closely"
echo "6. Keep source server running until fully verified"
echo ""
echo "Logs are available in: logs/"
echo "Migration data in: migration_data/"
echo ""
