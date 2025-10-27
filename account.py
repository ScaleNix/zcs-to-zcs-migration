"""Account class for managing Zimbra user accounts."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import os


@dataclass
class Account:
    """Represents a Zimbra user account."""
    
    mail: str
    mail_dst: str
    zimbra_mail_host: str
    is_migrated: bool = False
    is_exported: bool = False
    is_incr_migrated: bool = False
    is_incr_exported: bool = False
    is_ldiff_exported: bool = False
    is_ldiff_imported: bool = False
    root_folder: Path = field(default_factory=lambda: Path('.'))
    
    @property
    def account_folder(self) -> Path:
        """Get account's folder path."""
        return self.root_folder / self.mail
    
    @property
    def export_log_path(self) -> Path:
        """Get export log file path."""
        return self.account_folder / f"{self.mail}-export.log"
    
    @property
    def import_log_path(self) -> Path:
        """Get import log file path."""
        return self.account_folder / f"{self.mail}-import.log"
    
    @property
    def ldiff_path(self) -> Path:
        """Get LDIFF file path."""
        return self.account_folder / f"{self.mail}.ldiff"
    
    @property
    def backup_path(self) -> Path:
        """Get backup archive path."""
        return self.account_folder / f"{self.mail}.tgz"
    
    def create_folder(self) -> None:
        """Create account folder if it doesn't exist."""
        self.account_folder.mkdir(parents=True, exist_ok=True)
    
    def save_log(self, log: str, is_import: bool = False) -> None:
        """Save migration log.
        
        Args:
            log: Log content
            is_import: True for import log, False for export log
        """
        log_path = self.import_log_path if is_import else self.export_log_path
        log_path.write_text(log)
    
    def save_incr_log(self, log: str, is_import: bool = False) -> None:
        """Save incremental migration log.
        
        Args:
            log: Log content
            is_import: True for import log, False for export log
        """
        suffix = "incr-import.log" if is_import else "incr-export.log"
        log_path = self.account_folder / f"{self.mail}-{suffix}"
        log_path.write_text(log)
    
    def get_last_full_date(self) -> Optional[str]:
        """Get date of last full backup.
        
        Returns:
            Date string in MM/DD/YYYY format or None
        """
        if not self.backup_path.exists():
            return None
        
        mtime = datetime.fromtimestamp(self.backup_path.stat().st_mtime)
        last_date = mtime.strftime('%Y-%m-%d')
        yesterday = (datetime.strptime(last_date, '%Y-%m-%d') - timedelta(days=1))
        return yesterday.strftime('%m/%d/%Y')
    
    def __str__(self) -> str:
        """String representation."""
        return f"Account(mail={self.mail}, host={self.zimbra_mail_host})"