"""LDAP operations for Zimbra migration."""

import ldap
import logging
from typing import List, Tuple, Optional, Dict, Any
from account import Account


class LDAPHandler:
    """Handle LDAP operations for Zimbra."""
    
    def __init__(self, protocol: str, host: str, port: int, 
                 user: str, password: str, base_dn: str):
        """Initialize LDAP handler.
        
        Args:
            protocol: LDAP protocol (ldap:// or ldaps://)
            host: LDAP host
            port: LDAP port
            user: LDAP bind user
            password: LDAP bind password
            base_dn: LDAP base DN
        """
        self.protocol = protocol
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.base_dn = base_dn
        self.logger = logging.getLogger('zimbra_migration.ldap')
        self._conn: Optional[ldap.ldapobject.LDAPObject] = None
    
    def connect(self) -> ldap.ldapobject.LDAPObject:
        """Establish LDAP connection.
        
        Returns:
            LDAP connection object
            
        Raises:
            ldap.LDAPError: If connection fails
        """
        try:
            self.logger.info(f"Connecting to LDAP at {self.host}:{self.port}")
            ldap_url = f"{self.protocol}{self.host}:{self.port}/"
            conn = ldap.initialize(ldap_url)
            conn.set_option(ldap.OPT_REFERRALS, 0)
            conn.simple_bind_s(self.user, self.password)
            self._conn = conn
            return conn
        except ldap.LDAPError as e:
            self.logger.error(f"Failed to connect to LDAP: {e}")
            raise
    
    def search(self, filter_str: str, 
               base_dn: Optional[str] = None) -> List[Tuple[str, Dict[str, Any]]]:
        """Perform LDAP search.
        
        Args:
            filter_str: LDAP filter string
            base_dn: Base DN for search (uses default if None)
            
        Returns:
            List of search results
        """
        if not self._conn:
            self.connect()
        
        search_base = base_dn or self.base_dn
        self.logger.debug(f"Searching LDAP with filter: {filter_str}")
        
        result_id = self._conn.search(search_base, ldap.SCOPE_SUBTREE, filter_str)
        result_type, result_data = self._conn.result(result_id)
        
        return result_data
    
    def get_accounts(self, filter_str: str, root_folder: str) -> List[Account]:
        """Get accounts from LDAP.
        
        Args:
            filter_str: LDAP filter
            root_folder: Root folder for accounts
            
        Returns:
            List of Account objects
        """
        results = self.search(filter_str)
        accounts = []
        
        for dn, attrs in results:
            if 'zimbraMailDeliveryAddress' in attrs and 'zimbraMailHost' in attrs:
                mail = attrs['zimbraMailDeliveryAddress'][0].decode('utf-8')
                host = attrs['zimbraMailHost'][0].decode('utf-8')
                
                account = Account(
                    mail=mail,
                    mail_dst=mail,
                    zimbra_mail_host=host,
                    root_folder=root_folder
                )
                accounts.append(account)
                self.logger.debug(f"Created account object for {mail}")
        
        return accounts
    
    def user_exists(self, mail: str, filter_str: str) -> bool:
        """Check if user exists in LDAP.
        
        Args:
            mail: Email address
            filter_str: LDAP filter
            
        Returns:
            True if user exists, False otherwise
        """
        results = self.search(filter_str)
        for dn, attrs in results:
            if 'zimbraMailDeliveryAddress' in attrs:
                addr = attrs['zimbraMailDeliveryAddress'][0].decode('utf-8')
                if addr == mail:
                    return True
        return False
    
    def get_zimbra_host(self, mail: str, filter_str: str) -> Optional[str]:
        """Get Zimbra mail host for user.
        
        Args:
            mail: Email address
            filter_str: LDAP filter
            
        Returns:
            Zimbra mail host or None
        """
        results = self.search(filter_str)
        for dn, attrs in results:
            if 'zimbraMailDeliveryAddress' in attrs:
                addr = attrs['zimbraMailDeliveryAddress'][0].decode('utf-8')
                if addr == mail and 'zimbraMailHost' in attrs:
                    return attrs['zimbraMailHost'][0].decode('utf-8')
        return None
    
    def close(self) -> None:
        """Close LDAP connection."""
        if self._conn:
            self._conn.unbind_s()
            self._conn = None