"""Threading and migration orchestration."""

import threading
import logging
from typing import List, Optional
from pathlib import Path
from account import Account
from backup_manager import BackupManager
from ldap_handler import LDAPHandler


class SessionManager:
    """Thread-safe session management."""
    
    def __init__(self, session_file: Path):
        """Initialize session manager.
        
        Args:
            session_file: Path to session file
        """
        self.session_file = session_file
        self.lock = threading.Lock()
        self.logger = logging.getLogger('zimbra_migration.session')
    
    def record_session(self, account_mail: str, information: str) -> None:
        """Record session information.
        
        Args:
            account_mail: Account email
            information: Session information
        """
        with self.lock:
            try:
                with open(self.session_file, 'a') as f:
                    f.write(f"{account_mail};{information}\n")
                self.logger.debug(f"Recorded session for {account_mail}: {information}")
            except Exception as e:
                self.logger.error(f"Failed to record session: {e}")
    
    def check_session(self, account_mail: str, session_type: str) -> bool:
        """Check if session exists.
        
        Args:
            account_mail: Account email
            session_type: Session type to check
            
        Returns:
            True if session exists, False otherwise
        """
        if not self.session_file.exists():
            return False
        
        with self.lock:
            try:
                with open(self.session_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split(';')
                        if len(parts) >= 2 and parts[0] == account_mail:
                            if parts[1].startswith(session_type):
                                return True
            except Exception as e:
                self.logger.error(f"Failed to check session: {e}")
        
        return False


class MigrationWorker(threading.Thread):
    """Worker thread for migration tasks."""
    
    def __init__(self, thread_id: int, name: str, accounts: List[Account],
                 backup_manager: BackupManager, session_manager: SessionManager,
                 store_destinations: List[str], store_index: int,
                 do_full: bool = False, do_incr: bool = False, 
                 do_ldiff: bool = False, inc_date: Optional[str] = None):
        """Initialize migration worker.
        
        Args:
            thread_id: Thread ID
            name: Thread name
            accounts: List of accounts to process
            backup_manager: BackupManager instance
            session_manager: SessionManager instance
            store_destinations: List of destination stores
            store_index: Index of store to use
            do_full: Whether to perform full migration
            do_incr: Whether to perform incremental migration
            do_ldiff: Whether to perform LDIFF migration
            inc_date: Incremental date
        """
        super().__init__()
        self.thread_id = thread_id
        self.name = name
        self.accounts = accounts
        self.backup_manager = backup_manager
        self.session_manager = session_manager
        self.store_destinations = store_destinations
        self.store_index = store_index
        self.do_full = do_full
        self.do_incr = do_incr
        self.do_ldiff = do_ldiff
        self.inc_date = inc_date
        self.logger = logging.getLogger(f'zimbra_migration.worker.{name}')
    
    def run(self) -> None:
        """Run migration tasks."""
        self.logger.info(f"Starting {self.name} with {len(self.accounts)} accounts")
        
        try:
            if self.do_ldiff:
                self._process_ldiff()
            
            if self.do_full:
                self._process_full_migration()
            
            if self.do_incr:
                self._process_incremental_migration()
                
        except Exception as e:
            self.logger.error(f"Worker {self.name} failed: {e}", exc_info=True)
        finally:
            self.logger.info(f"Exiting {self.name}")
    
    def _process_ldiff(self) -> None:
        """Process LDIFF export/import."""
        self.logger.info("Processing LDIFF operations")
        
        target_store = self.store_destinations[self.store_index] if self.store_destinations else None
        
        for account in self.accounts:
            # Export LDIFF
            self.backup_manager.export_ldiff(account, self._get_source_ldap_config())
            
            if account.is_ldiff_exported and target_store:
                # Modify for load balancing
                self.backup_manager.modify_ldiff_for_load_balancing(account, target_store)
                
                # Import LDIFF
                self.backup_manager.import_ldiff(account, self._get_dest_ldap_config())
    
    def _process_full_migration(self) -> None:
        """Process full migration."""
        self.logger.info("Processing full migration")
        
        for account in self.accounts:
            # Check session
            if self.session_manager.check_session(account.mail, "FULL-EXPORT"):
                self.logger.info(f"Account {account.mail} already has full backup")
                account.is_exported = True
                continue
            
            # Export full backup
            if self.backup_manager.export_full_backup(account):
                last_full_date = account.get_last_full_date()
                if last_full_date:
                    self.session_manager.record_session(
                        account.mail, f"FULL-EXPORT;{last_full_date}"
                    )
        
        # Import full backups
        for account in self.accounts:
            if self.session_manager.check_session(account.mail, "FULL-IMPORT"):
                self.logger.info(f"Account {account.mail} already imported")
                account.is_migrated = True
                continue
            
            if account.is_exported:
                host = account.zimbra_mail_host
                if self.backup_manager.import_full_backup(account, host):
                    last_full_date = account.get_last_full_date()
                    if last_full_date:
                        self.session_manager.record_session(
                            account.mail, f"FULL-IMPORT;{last_full_date}"
                        )
    
    def _process_incremental_migration(self) -> None:
        """Process incremental migration."""
        self.logger.info("Processing incremental migration")
        
        for account in self.accounts:
            inc_date = self.inc_date or account.get_last_full_date()
            
            if not inc_date:
                self.logger.warning(f"No full backup date for {account.mail}, skipping")
                continue
            
            # Export incremental backup
            self.backup_manager.export_incremental_backup(account, inc_date)
            
            if account.is_incr_exported:
                self.session_manager.record_session(
                    account.mail, f"INCR-EXPORT;{inc_date}"
                )
        
        # Import incremental backups
        for account in self.accounts:
            inc_date = self.inc_date or account.get_last_full_date()
            
            if not inc_date:
                continue
            
            host = account.zimbra_mail_host
            if self.backup_manager.import_incremental_backup(account, inc_date, host):
                self.session_manager.record_session(
                    account.mail, f"INCR-IMPORT;{inc_date}"
                )
    
    def _get_source_ldap_config(self) -> dict:
        """Get source LDAP config (to be implemented with actual config)."""
        # This should come from ConfigManager
        return {}
    
    def _get_dest_ldap_config(self) -> dict:
        """Get destination LDAP config (to be implemented with actual config)."""
        # This should come from ConfigManager
        return {}