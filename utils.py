"""Utility functions for Zimbra migration."""

import csv
from typing import List, Dict
from pathlib import Path
from datetime import datetime, timedelta
from account import Account
import logging


class DateValidator:
    """Validate and parse dates."""
    
    @staticmethod
    def validate_date(date_str: str, format_str: str = '%m/%d/%Y') -> bool:
        """Validate date string.
        
        Args:
            date_str: Date string to validate
            format_str: Expected date format
            
        Returns:
            True if valid, False otherwise
        """
        try:
            datetime.strptime(date_str, format_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def get_auto_incr_date(days_back: int = 5) -> str:
        """Get automatic incremental date.
        
        Args:
            days_back: Number of days to go back
            
        Returns:
            Date string in MM/DD/YYYY format
        """
        target_date = datetime.now() - timedelta(days=days_back)
        return target_date.strftime('%m/%d/%Y')
    
    @staticmethod
    def should_run_incremental(inc_date: str) -> bool:
        """Check if incremental should run.
        
        Args:
            inc_date: Incremental date string
            
        Returns:
            True if incremental should run, False otherwise
        """
        yesterday = datetime.now() - timedelta(days=1)
        inc_datetime = datetime.strptime(inc_date, '%m/%d/%Y')
        
        return inc_datetime.date() <= yesterday.date()


class CSVAccountLoader:
    """Load accounts from CSV file."""
    
    def __init__(self, logger: logging.Logger):
        """Initialize CSV loader.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
    
    def load_accounts(self, csv_path: Path, store_mapping: Dict[str, str],
                     root_folder: Path) -> List[Account]:
        """Load accounts from CSV file.
        
        Args:
            csv_path: Path to CSV file
            store_mapping: Mapping of destination emails to hosts
            root_folder: Root folder for accounts
            
        Returns:
            List of Account objects
        """
        accounts = []
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f, delimiter=';')
                for row in reader:
                    if len(row) >= 2:
                        source_mail = row[0].strip()
                        dest_mail = row[1].strip()
                        host = store_mapping.get(dest_mail, 'localhost')
                        
                        account = Account(
                            mail=source_mail,
                            mail_dst=dest_mail,
                            zimbra_mail_host=host,
                            root_folder=root_folder
                        )
                        accounts.append(account)
                        self.logger.debug(f"Loaded account from CSV: {source_mail}")
        except Exception as e:
            self.logger.error(f"Failed to load accounts from CSV: {e}")
            raise
        
        return accounts


class StoreMappingLoader:
    """Load store mappings from CSV."""
    
    @staticmethod
    def load_mapping(csv_path: Path) -> Dict[str, str]:
        """Load store mapping from CSV file.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            Dictionary mapping emails to hosts
        """
        mapping = {}
        
        with open(csv_path, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                if len(row) >= 2:
                    email = row[0].strip()
                    host = row[1].strip()
                    mapping[email] = host
        
        return mapping


class MigrationStatistics:
    """Generate migration statistics."""
    
    def __init__(self, accounts: List[Account]):
        """Initialize statistics generator.
        
        Args:
            accounts: List of accounts
        """
        self.accounts = accounts
    
    def print_full_migrated(self) -> None:
        """Print accounts that were fully migrated."""
        print('\n' + '='*60)
        print('ACCOUNTS FULLY MIGRATED')
        print('='*60)
        
        for account in self.accounts:
            if account.is_migrated:
                print(f"  ✓ {account.mail}")
                last_full = account.get_last_full_date()
                if last_full:
                    print(f"    Last full backup: {last_full}")
        
        print('='*60 + '\n')
    
    def print_full_not_migrated(self) -> None:
        """Print accounts that were not fully migrated."""
        print('\n' + '='*60)
        print('ACCOUNTS NOT FULLY MIGRATED')
        print('='*60)
        
        for account in self.accounts:
            if not account.is_migrated:
                print(f"  ✗ {account.mail}")
                last_full = account.get_last_full_date()
                if last_full:
                    print(f"    Last full backup: {last_full}")
                    print(f"    → Please start new full migration")
        
        print('='*60 + '\n')
    
    def print_incr_migrated(self) -> None:
        """Print accounts with incremental migration."""
        print('\n' + '='*60)
        print('ACCOUNTS INCREMENTALLY MIGRATED')
        print('='*60)
        
        for account in self.accounts:
            if account.is_incr_migrated:
                print(f"  ✓ {account.mail}")
        
        print('='*60 + '\n')
    
    def print_incr_not_migrated(self) -> None:
        """Print accounts without incremental migration."""
        print('\n' + '='*60)
        print('ACCOUNTS NOT INCREMENTALLY MIGRATED')
        print('='*60)
        
        for account in self.accounts:
            if not account.is_incr_migrated:
                print(f"  ✗ {account.mail}")
        
        print('='*60 + '\n')
    
    def print_summary(self) -> None:
        """Print migration summary."""
        total = len(self.accounts)
        full_migrated = sum(1 for a in self.accounts if a.is_migrated)
        incr_migrated = sum(1 for a in self.accounts if a.is_incr_migrated)
        ldiff_exported = sum(1 for a in self.accounts if a.is_ldiff_exported)
        
        print('\n' + '='*60)
        print('MIGRATION SUMMARY')
        print('='*60)
        print(f"  Total accounts:           {total}")
        print(f"  LDIFF exported:           {ldiff_exported}")
        print(f"  Fully migrated:           {full_migrated}")
        print(f"  Incrementally migrated:   {incr_migrated}")
        print('='*60 + '\n')