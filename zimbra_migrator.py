#!/usr/bin/env python3
"""Main entry point for Zimbra migration tool."""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional

from config_manager import ConfigManager
from logger_config import LoggerConfig
from ldap_handler import LDAPHandler
from backup_manager import BackupManager
from migration_worker import MigrationWorker, SessionManager
from utils import (
    DateValidator, CSVAccountLoader, StoreMappingLoader, MigrationStatistics
)
from account import Account


class ZimbraMigrator:
    """Main Zimbra migration orchestrator."""
    
    def __init__(self, config_path: str = "config.ini"):
        """Initialize Zimbra migrator.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = ConfigManager(config_path)
        self.logger = LoggerConfig.setup_logger(
            self.config.log_level,
            'activity-migration.log'
        )
        self.logger = logging.getLogger('zimbra_migration')
        
        # Initialize session manager
        self.session_manager = SessionManager(self.config.session_file)
        
        # Initialize LDAP handlers
        src_cfg = self.config.source
        self.source_ldap = LDAPHandler(
            protocol=src_cfg['ldap_protocol'],
            host=src_cfg['ldap_host'],
            port=int(src_cfg['ldap_port']),
            user=src_cfg['ldap_user'],
            password=src_cfg['ldap_pass'],
            base_dn=src_cfg['ldap_base_dn']
        )
        
        # Initialize backup manager
        self.port_mapping = {"localhost": 7071}
        self.backup_manager = BackupManager(
            source_host=src_cfg['host'],
            dest_host=self.config.destination['host'],
            source_admin=src_cfg['admin_user'],
            source_pass=src_cfg['admin_password'],
            dest_admin=self.config.destination['admin_user'],
            dest_pass=self.config.destination['admin_password'],
            port_mapping=self.port_mapping
        )
        
        # Store destinations
        self.store_destinations = ['test']  # TODO: Get from LDAP
        
        # Store mapping
        self.store_mapping = {}
    
    def setup_environment(self) -> bool:
        """Setup environment (create folders, etc.).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create root folder
            self.config.root_folder.mkdir(parents=True, exist_ok=True)
            
            # Create session file
            self.config.session_file.touch(exist_ok=True)
            
            self.logger.info("Environment setup completed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup environment: {e}")
            return False
    
    def load_accounts_from_ldap(self, filter_str: str) -> List[Account]:
        """Load accounts from LDAP.
        
        Args:
            filter_str: LDAP filter string
            
        Returns:
            List of Account objects
        """
        self.logger.info("Loading accounts from LDAP")
        accounts = self.source_ldap.get_accounts(
            filter_str,
            str(self.config.root_folder)
        )
        self.logger.info(f"Loaded {len(accounts)} accounts from LDAP")
        return accounts
    
    def load_accounts_from_csv(self, csv_path: str) -> List[Account]:
        """Load accounts from CSV file.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of Account objects
        """
        self.logger.info(f"Loading accounts from CSV: {csv_path}")
        loader = CSVAccountLoader(self.logger)
        accounts = loader.load_accounts(
            Path(csv_path),
            self.store_mapping,
            self.config.root_folder
        )
        self.logger.info(f"Loaded {len(accounts)} accounts from CSV")
        return accounts
    
    def load_store_mapping(self, csv_path: str) -> None:
        """Load store mapping from CSV.
        
        Args:
            csv_path: Path to CSV file
        """
        self.logger.info(f"Loading store mapping from: {csv_path}")
        self.store_mapping = StoreMappingLoader.load_mapping(Path(csv_path))
        self.logger.info(f"Loaded {len(self.store_mapping)} store mappings")
    
    def run_migration(self, accounts: List[Account], num_threads: int,
                     store_index: int, do_full: bool, do_incr: bool,
                     do_ldiff: bool, inc_date: Optional[str]) -> None:
        """Run migration with threading.
        
        Args:
            accounts: List of accounts to migrate
            num_threads: Number of threads to use
            store_index: Index of destination store
            do_full: Whether to perform full migration
            do_incr: Whether to perform incremental migration
            do_ldiff: Whether to perform LDIFF migration
            inc_date: Incremental date
        """
        self.logger.info(f"Starting migration with {num_threads} thread(s)")
        
        if num_threads == 1:
            # Single-threaded execution
            worker = MigrationWorker(
                thread_id=0,
                name="MainThread",
                accounts=accounts,
                backup_manager=self.backup_manager,
                session_manager=self.session_manager,
                store_destinations=self.store_destinations,
                store_index=store_index,
                do_full=do_full,
                do_incr=do_incr,
                do_ldiff=do_ldiff,
                inc_date=inc_date
            )
            worker.run()
        else:
            # Multi-threaded execution
            accounts_per_thread = len(accounts) // num_threads
            threads = []
            
            for i in range(num_threads):
                start_idx = i * accounts_per_thread
                end_idx = start_idx + accounts_per_thread if i < num_threads - 1 else len(accounts)
                thread_accounts = accounts[start_idx:end_idx]
                
                worker = MigrationWorker(
                    thread_id=i,
                    name=f"Thread-{i}",
                    accounts=thread_accounts,
                    backup_manager=self.backup_manager,
                    session_manager=self.session_manager,
                    store_destinations=self.store_destinations,
                    store_index=store_index,
                    do_full=do_full,
                    do_incr=do_incr,
                    do_ldiff=do_ldiff,
                    inc_date=inc_date
                )
                worker.start()
                threads.append(worker)
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
        
        self.logger.info("Migration completed")
    
    def print_statistics(self, accounts: List[Account]) -> None:
        """Print migration statistics.
        
        Args:
            accounts: List of accounts
        """
        stats = MigrationStatistics(accounts)
        stats.print_summary()
        stats.print_full_migrated()
        stats.print_full_not_migrated()
        stats.print_incr_migrated()
        stats.print_incr_not_migrated()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Zimbra to Zimbra Migration Tool (Refactored)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Source options
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        '-ldap', '--ldap',
        action='store_true',
        help='Load accounts from LDAP'
    )
    source_group.add_argument(
        '-s', '--source',
        help='Load accounts from CSV file'
    )
    
    # Migration options
    parser.add_argument(
        '-f', '--full',
        action='store_true',
        help='Perform full migration'
    )
    parser.add_argument(
        '-i', '--incr',
        action='store_true',
        help='Perform incremental migration'
    )
    parser.add_argument(
        '-l', '--ldiff',
        action='store_true',
        help='Perform LDIFF export/import'
    )
    
    # Threading and store options
    parser.add_argument(
        '-t', '--thread',
        type=int,
        required=True,
        help='Number of threads to use'
    )
    parser.add_argument(
        '-d', '--destination-store',
        type=int,
        default=1,
        help='Destination store index (default: 1)'
    )
    
    # Incremental options
    parser.add_argument(
        '-at', '--at-time',
        help='Incremental date (MM/DD/YYYY) or "cron" for auto'
    )
    
    # Other options
    parser.add_argument(
        '-b', '--l-destination-store',
        action='store_true',
        help='List all destination stores'
    )
    parser.add_argument(
        '-c', '--config',
        default='config.ini',
        help='Path to configuration file (default: config.ini)'
    )
    
    args = parser.parse_args()
    
    # Initialize migrator
    try:
        migrator = ZimbraMigrator(args.config)
    except Exception as e:
        print(f"Failed to initialize migrator: {e}")
        sys.exit(1)
    
    # Setup environment
    if not migrator.setup_environment():
        sys.exit(1)
    
    # List stores if requested
    if args.l_destination_store:
        print("\nAvailable Destination Stores:")
        print("=" * 60)
        for idx, store in enumerate(migrator.store_destinations, 1):
            print(f"  [{idx}] {store}")
        print("=" * 60)
        sys.exit(0)
    
    # Validate migration options
    if not (args.full or args.incr or args.ldiff):
        parser.error("At least one migration option (-f, -i, -l) is required")
    
    # Handle incremental date
    inc_date = None
    if args.incr:
        if args.at_time:
            if args.at_time == "cron":
                inc_date = DateValidator.get_auto_incr_date()
            else:
                if not DateValidator.validate_date(args.at_time):
                    parser.error("Invalid date format. Use MM/DD/YYYY")
                inc_date = args.at_time
    
    # Load store mapping
    migrator.load_store_mapping("zimbra_mail_hosts.csv")
    
    # Load accounts
    try:
        if args.ldap:
            accounts = migrator.load_accounts_from_ldap(
                migrator.config.source['ldap_filter']
            )
        else:
            accounts = migrator.load_accounts_from_csv(args.source)
    except Exception as e:
        migrator.logger.error(f"Failed to load accounts: {e}")
        sys.exit(1)
    
    if not accounts:
        migrator.logger.error("No accounts loaded")
        sys.exit(1)
    
    # Run migration
    store_index = args.destination_store - 1
    try:
        migrator.run_migration(
            accounts=accounts,
            num_threads=args.thread,
            store_index=store_index,
            do_full=args.full,
            do_incr=args.incr,
            do_ldiff=args.ldiff,
            inc_date=inc_date
        )
    except Exception as e:
        migrator.logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)
    
    # Print statistics
    migrator.print_statistics(accounts)


if __name__ == "__main__":
    main()