"""
Configuration management for Spotify integration.

:copyright: (c) 2024
:license: MPL-2.0, see LICENSE for more details.
"""

import json
import logging
import time
from typing import Any, Dict, Optional

_LOG = logging.getLogger(__name__)


class SpotifyConfig:
    """Configuration management for Spotify integration."""
    
    def __init__(self, config_file_path: str):
        """Initialize configuration with file path."""
        self._config_file_path = config_file_path
        self._config_data: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            with open(self._config_file_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
            _LOG.debug("Configuration loaded successfully")
        except FileNotFoundError:
            _LOG.debug("Configuration file not found, starting with empty config")
            self._config_data = {}
        except json.JSONDecodeError as e:
            _LOG.error("Error parsing configuration file: %s", e)
            self._config_data = {}
        except Exception as e:
            _LOG.error("Error loading configuration: %s", e)
            self._config_data = {}
    
    def _save_config(self) -> bool:
        """Save configuration to file."""
        try:
            with open(self._config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
            _LOG.debug("Configuration saved successfully")
            return True
        except Exception as e:
            _LOG.error("Error saving configuration: %s", e)
            return False
    
    def is_configured(self) -> bool:
        """Check if the integration is configured with valid tokens and app credentials."""
        access_token = self.get_access_token()
        refresh_token = self.get_refresh_token()
        client_id = self.get_client_id()
        client_secret = self.get_client_secret()
        return all([access_token, refresh_token, client_id, client_secret])
    
    def set_app_credentials(self, client_id: str, client_secret: str) -> bool:
        """
        Set Spotify app credentials.
        
        Args:
            client_id: Spotify app client ID
            client_secret: Spotify app client secret
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self._config_data["client_id"] = client_id
            self._config_data["client_secret"] = client_secret
            return self._save_config()
        except Exception as e:
            _LOG.error("Error setting app credentials: %s", e)
            return False
    
    def get_client_id(self) -> Optional[str]:
        """Get the Spotify app client ID."""
        return self._config_data.get("client_id")
    
    def get_client_secret(self) -> Optional[str]:
        """Get the Spotify app client secret."""
        return self._config_data.get("client_secret")
    
    def set_tokens(self, access_token: str, refresh_token: str, expires_in: int) -> bool:
        """
        Set OAuth2 tokens.
        
        Args:
            access_token: Spotify access token
            refresh_token: Spotify refresh token
            expires_in: Token expiration time in seconds
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self._config_data["access_token"] = access_token
            self._config_data["refresh_token"] = refresh_token
            self._config_data["token_expires_at"] = int(time.time()) + expires_in - 60  # 60 second buffer
            
            return self._save_config()
        except Exception as e:
            _LOG.error("Error setting tokens: %s", e)
            return False
    
    def get_access_token(self) -> Optional[str]:
        """Get the current access token."""
        return self._config_data.get("access_token")
    
    def get_refresh_token(self) -> Optional[str]:
        """Get the current refresh token."""
        return self._config_data.get("refresh_token")
    
    def is_token_expired(self) -> bool:
        """Check if the access token is expired."""
        expires_at = self._config_data.get("token_expires_at", 0)
        return int(time.time()) >= expires_at
    
    def set_premium_user(self, is_premium: bool) -> bool:
        """
        Set whether the user has Spotify Premium.
        
        Args:
            is_premium: True if user has Premium, False otherwise
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self._config_data["is_premium"] = is_premium
            return self._save_config()
        except Exception as e:
            _LOG.error("Error setting premium status: %s", e)
            return False
    
    def is_premium_user(self) -> bool:
        """Check if the user has Spotify Premium."""
        return self._config_data.get("is_premium", False)
    
    def get_polling_interval(self) -> int:
        """Get the polling interval in seconds."""
        return self._config_data.get("polling_interval", 30)
    
    def set_polling_interval(self, interval: int) -> bool:
        """
        Set the polling interval.
        
        Args:
            interval: Polling interval in seconds
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self._config_data["polling_interval"] = max(10, min(300, interval))  # Between 10s and 5min
            return self._save_config()
        except Exception as e:
            _LOG.error("Error setting polling interval: %s", e)
            return False
    
    def clear_tokens(self) -> bool:
        """Clear all stored tokens."""
        try:
            self._config_data.pop("access_token", None)
            self._config_data.pop("refresh_token", None)
            self._config_data.pop("token_expires_at", None)
            return self._save_config()
        except Exception as e:
            _LOG.error("Error clearing tokens: %s", e)
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration data (for debugging)."""
        # Return a copy without sensitive data
        safe_config = self._config_data.copy()
        if "access_token" in safe_config:
            safe_config["access_token"] = "***HIDDEN***"
        if "refresh_token" in safe_config:
            safe_config["refresh_token"] = "***HIDDEN***"
        if "client_secret" in safe_config:
            safe_config["client_secret"] = "***HIDDEN***"
        return safe_config
    
    def reset_config(self) -> bool:
        """Reset all configuration data."""
        try:
            self._config_data = {}
            return self._save_config()
        except Exception as e:
            _LOG.error("Error resetting configuration: %s", e)
            return False