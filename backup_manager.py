"""Backup and restore operations for Zimbra migration."""

import subprocess
import logging
from typing import Optional, List
from pathlib import Path
from datetime import datetime
from account import Account


class BackupManager:
    """Manages backup and restore operations for Zimbra accounts."""
    
    def __init__(self, source_host: str, dest_host: str,
                 source_admin: str, source_pass: str,
                 dest_admin: str, dest_pass: str,
                 port_mapping: dict):
        """Initialize backup manager.
        
        Args:
            source_host: Source Zimbra host
            dest_host: Destination Zimbra host
            source_admin: Source admin username
            source_pass: Source admin password
            dest_admin: Destination admin username
            dest_pass: Destination admin password
            port_mapping: Host to port mapping
        """
        self.source_host = source_host
        self.dest_host = dest_host
        self.source_admin = source_admin
        self.source_pass = source_pass
        self.dest_admin = dest_admin
        self.dest_pass = dest_pass
        self.port_mapping = port_mapping
        self.logger = logging.getLogger('zimbra_migration.backup')
    
    def _execute_command(self, command: List[str]) -> tuple[int, str]:
        """Execute shell command.
        
        Args:
            command: Command as list of strings
            
        Returns:
            Tuple of (return_code, output)
        """
        try:
            self.logger.debug(f"Executing command: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                shell=False
            )
            return result.returncode, result.stdout + result.stderr
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return 1, str(e)
    
    def _verify_curl_response(self, output: str) -> bool:
        """Verify curl command was successful.
        
        Args:
            output: Curl command output
            
        Returns:
            True if successful, False otherwise
        """
        success_messages = ["HTTP/1.1 200 OK", "HTTP/1.1 204 No Content"]
        error_message = "500 Server Error"
        
        has_success = any(msg in output for msg in success_messages)
        has_error = error_message in output
        
        return has_success and not has_error
    
    def export_ldiff(self, account: Account, ldap_config: dict) -> bool:
        """Export LDIFF for account.
        
        Args:
            account: Account object
            ldap_config: LDAP configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Exporting LDIFF for {account.mail}")
        account.create_folder()
        
        ldap_url = f"{ldap_config['ldap_protocol']}{ldap_config['ldap_host']}:{ldap_config['ldap_port']}"
        
        command = [
            "/opt/zimbra/common/bin/ldapsearch",
            "-x",
            "-H", ldap_url,
            "-D", ldap_config['ldap_user'],
            "-w", ldap_config['ldap_pass'],
            f"(mail={account.mail})",
            "-LLLLL"
        ]
        
        returncode, output = self._execute_command(command)
        
        if returncode == 0:
            account.ldiff_path.write_text(output)
            self.logger.info(f"LDIFF exported successfully for {account.mail}")
            account.is_ldiff_exported = True
            return True
        else:
            self.logger.error(f"Failed to export LDIFF for {account.mail}")
            self.logger.debug(output)
            account.is_ldiff_exported = False
            return False
    
    def import_ldiff(self, account: Account, ldap_config: dict) -> bool:
        """Import LDIFF for account.
        
        Args:
            account: Account object
            ldap_config: Destination LDAP configuration
            
        Returns:
            True if successful, False otherwise
        """
        if not account.is_ldiff_exported:
            self.logger.warning(f"LDIFF not exported for {account.mail}, skipping import")
            return False
        
        self.logger.info(f"Importing LDIFF for {account.mail}")
        
        ldap_url = f"ldap://{ldap_config['ldap_host']}:{ldap_config['ldap_port']}"
        
        command = [
            "/opt/zimbra/common/bin/ldapadd",
            "-x",
            "-H", ldap_url,
            "-D", ldap_config['ldap_user'],
            "-w", ldap_config['ldap_pass'],
            "-f", str(account.ldiff_path)
        ]
        
        returncode, output = self._execute_command(command)
        
        if returncode == 0:
            self.logger.info(f"LDIFF imported successfully for {account.mail}")
            account.is_ldiff_imported = True
            return True
        else:
            self.logger.error(f"Failed to import LDIFF for {account.mail}")
            self.logger.debug(output)
            account.is_ldiff_imported = False
            return False
    
    def export_full_backup(self, account: Account) -> bool:
        """Export full backup for account.
        
        Args:
            account: Account object
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Exporting full backup for {account.mail}")
        account.create_folder()
        
        url = f"https://{self.source_host}:7071/home/{account.mail}/?fmt=tgz"
        
        command = [
            "curl",
            "-kvv",
            "-u", f"{self.source_admin}:{self.source_pass}",
            "--insecure",
            url,
            "-o", str(account.backup_path)
        ]
        
        returncode, output = self._execute_command(command)
        
        if self._verify_curl_response(output):
            self.logger.info(f"Full backup exported successfully for {account.mail}")
            account.save_log(output, is_import=False)
            account.is_exported = True
            return True
        else:
            self.logger.error(f"Failed to export full backup for {account.mail}")
            self.logger.debug(output)
            account.save_log(output, is_import=False)
            account.is_exported = False
            return False
    
    def import_full_backup(self, account: Account, host: str) -> bool:
        """Import full backup for account.
        
        Args:
            account: Account object
            host: Destination host
            
        Returns:
            True if successful, False otherwise
        """
        if not account.is_exported:
            self.logger.warning(f"Backup not exported for {account.mail}, skipping import")
            return False
        
        self.logger.info(f"Importing full backup for {account.mail}")
        
        port = str(self.port_mapping.get(host, 7071))
        url = f"https://{host}:{port}/home/{account.mail_dst}/?fmt=tgz&resolve=skip"
        
        command = [
            "curl",
            "-kvv",
            "--upload-file", str(account.backup_path),
            "-u", f"{self.dest_admin}:{self.dest_pass}",
            url
        ]
        
        returncode, output = self._execute_command(command)
        
        if self._verify_curl_response(output):
            self.logger.info(f"Full backup imported successfully for {account.mail}")
            account.save_log(output, is_import=True)
            account.is_migrated = True
            return True
        else:
            self.logger.error(f"Failed to import full backup for {account.mail}")
            self.logger.debug(output)
            account.save_log(output, is_import=True)
            account.is_migrated = False
            return False
    
    def export_incremental_backup(self, account: Account, inc_date: str) -> bool:
        """Export incremental backup for account.
        
        Args:
            account: Account object
            inc_date: Incremental date (MM/DD/YYYY format)
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Exporting incremental backup for {account.mail} from {inc_date}")
        account.create_folder()
        
        inc_filename = f"{account.mail}-{inc_date.replace('/', '-')}.tgz"
        inc_path = account.account_folder / inc_filename
        
        url = f"https://{self.source_host}:7071/home/{account.mail}/?fmt=tgz&query=after:{inc_date}"
        
        command = [
            "curl",
            "-kvv",
            "-u", f"{self.source_admin}:{self.source_pass}",
            "--insecure",
            url,
            "-o", str(inc_path)
        ]
        
        returncode, output = self._execute_command(command)
        
        if self._verify_curl_response(output):
            self.logger.info(f"Incremental backup exported successfully for {account.mail}")
            account.save_incr_log(output, is_import=False)
            account.is_incr_exported = True
            return True
        else:
            self.logger.error(f"Failed to export incremental backup for {account.mail}")
            self.logger.debug(output)
            account.save_incr_log(output, is_import=False)
            account.is_incr_exported = False
            return False
    
    def import_incremental_backup(self, account: Account, inc_date: str, host: str) -> bool:
        """Import incremental backup for account.
        
        Args:
            account: Account object
            inc_date: Incremental date (MM/DD/YYYY format)
            host: Destination host
            
        Returns:
            True if successful, False otherwise
        """
        inc_filename = f"{account.mail}-{inc_date.replace('/', '-')}.tgz"
        inc_path = account.account_folder / inc_filename
        
        # Check if file is empty (no changes)
        if inc_path.stat().st_size == 0:
            self.logger.info(f"No incremental changes for {account.mail}")
            account.is_incr_migrated = True
            self._perform_cutover(account)
            return True
        
        self.logger.info(f"Importing incremental backup for {account.mail}")
        
        port = str(self.port_mapping.get(host, 7071))
        url = f"https://{host}:{port}/home/{account.mail_dst}/?fmt=tgz&resolve=skip"
        
        command = [
            "curl",
            "-kvv",
            "--data-binary", f"@{inc_path}",
            "-u", f"{self.dest_admin}:{self.dest_pass}",
            url
        ]
        
        returncode, output = self._execute_command(command)
        
        if self._verify_curl_response(output):
            self.logger.info(f"Incremental backup imported successfully for {account.mail}")
            account.save_incr_log(output, is_import=True)
            account.is_incr_migrated = True
            self._perform_cutover(account)
            return True
        else:
            self.logger.error(f"Failed to import incremental backup for {account.mail}")
            self.logger.debug(output)
            account.save_incr_log(output, is_import=True)
            account.is_incr_migrated = False
            return False
    
    def _perform_cutover(self, account: Account) -> None:
        """Perform cutover by updating canonical address.
        
        Args:
            account: Account object
        """
        self.logger.info(f"Performing cutover for {account.mail}")
        
        command = [
            "ssh", "zimbra-source",
            f"/opt/zimbra/bin/zmprov ma {account.mail} zimbraMailCanonicalAddress {account.mail_dst}"
        ]
        
        returncode, output = self._execute_command(command)
        
        if returncode == 0:
            self.logger.info(f"Cutover successful for {account.mail}")
        else:
            self.logger.error(f"Cutover failed for {account.mail}")
            self.logger.debug(output)
    
    def modify_ldiff_for_load_balancing(self, account: Account, target_store: str) -> bool:
        """Modify LDIFF file for load balancing.
        
        Args:
            account: Account object
            target_store: Target store name
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.debug(f"Modifying LDIFF for {account.mail} to use store {target_store}")
        
        ldiff_content = account.ldiff_path.read_text()
        
        # Modify zimbraMailHost
        lines = ldiff_content.split('\n')
        modified_lines = []
        
        for line in lines:
            if line.startswith('zimbraMailHost:'):
                modified_lines.append(f'zimbraMailHost: {target_store}')
            elif line.startswith('zimbraMailTransport:'):
                modified_lines.append(f'zimbraMailTransport: lmtp:{target_store}:7025')
            elif line.startswith('zimbraPrefChildVisibleAccount:'):
                # Skip this line (bug fix)
                continue
            else:
                modified_lines.append(line)
        
        account.ldiff_path.write_text('\n'.join(modified_lines))
        self.logger.debug(f"LDIFF modified successfully for {account.mail}")
        return True