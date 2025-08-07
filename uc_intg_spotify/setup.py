"""
Setup handler for Spotify integration.

:copyright: (c) 2024
:license: MPL-2.0, see LICENSE for more details.
"""
import logging
from typing import Any, Callable, Coroutine

import ucapi

from uc_intg_spotify.client import SpotifyClient
from uc_intg_spotify.config import SpotifyConfig

_LOG = logging.getLogger(__name__)


class SpotifySetup:
    """Setup handler for Spotify integration."""
    
    def __init__(self, config: SpotifyConfig, client: SpotifyClient, setup_complete_callback: Callable[[], Coroutine[Any, Any, None]]):
        self._config = config
        self._client = client
        self._setup_complete_callback = setup_complete_callback
    
    async def setup_handler(self, msg: ucapi.SetupDriver) -> ucapi.SetupAction:
        """Handle setup requests from Remote Two."""
        _LOG.info("Setup handler called with: %s", type(msg).__name__)
        
        if isinstance(msg, ucapi.DriverSetupRequest):
            return await self._handle_driver_setup_request(msg)
        elif isinstance(msg, ucapi.UserDataResponse):
            return await self._handle_user_data_response(msg)
        elif isinstance(msg, ucapi.AbortDriverSetup):
            return await self._handle_abort_setup(msg)
        
        return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)
    
    async def _handle_driver_setup_request(self, msg: ucapi.DriverSetupRequest) -> ucapi.SetupAction:
        """Handle initial setup request."""
        _LOG.debug("Handling driver setup request.")
        
        if self._config.is_configured() and not msg.reconfigure:
            _LOG.info("Already configured, proceeding to completion")
            await self._setup_complete_callback() 
            return ucapi.SetupComplete()
        
        if msg.setup_data:
            client_id = msg.setup_data.get("client_id", "").strip()
            client_secret = msg.setup_data.get("client_secret", "").strip()
            is_premium_raw = msg.setup_data.get("is_premium", False)
            
            # Convert checkbox value to boolean
            if isinstance(is_premium_raw, str):
                is_premium = is_premium_raw.lower() in ("true", "1", "yes", "on")
            else:
                is_premium = bool(is_premium_raw)
            
            if client_id and client_secret:
                _LOG.info("App credentials provided, proceeding to authentication")
                
                self._config.set_app_credentials(client_id, client_secret)
                self._config.set_premium_user(is_premium)
                
                return await self._show_authentication_screen()
            else:
                _LOG.error("Missing client ID or client secret in setup data")
                return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)
        
        _LOG.warning("No setup data provided")
        return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)
    
    async def _show_authentication_screen(self) -> ucapi.SetupAction:
        """Show the Spotify authentication screen."""
        _LOG.debug("Showing Spotify authentication screen.")
        
        try:
            auth_url = self._client.get_authorization_url()
        except ValueError as e:
            _LOG.error("Failed to generate auth URL: %s", e)
            return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)

        return ucapi.RequestUserInput(
            title={"en": "Spotify Authentication"},
            settings=[
                {
                    "id": "instructions",
                    "label": {"en": "Authentication Instructions"},
                    "field": {
                        "label": {
                            "value": {
                                "en": "1. Click the Spotify URL below to open it in a new browser tab\n2. Log in to your Spotify account and authorize this application\n3. Your browser will show 'page not found' - this is normal!\n4. Look at your browser's address bar and find 'code=...'\n5. Copy the long code after 'code=' and paste it below"
                            }
                        }
                    }
                },
                {
                    "id": "spotify_url",
                    "label": {"en": "Spotify Authorization URL (Click to Copy)"},
                    "field": {
                        "text": {
                            "value": auth_url,
                            "read_only": True
                        }
                    }
                },
                {
                    "id": "auth_code",
                    "label": {"en": "Paste Code or Full URL Here"},
                    "field": {
                        "text": {
                            "value": "",
                            "placeholder": "Paste the code or entire URL from your browser here..."
                        }
                    }
                }
            ]
        )
    
    async def _handle_user_data_response(self, msg: ucapi.UserDataResponse) -> ucapi.SetupAction:
        """Handle the submitted authorization code."""
        _LOG.debug("Handling user data response: %s", msg.input_values)
        
        auth_input = msg.input_values.get("auth_code", "").strip()
        
        if not auth_input:
            _LOG.error("Authorization code is missing from user input.")
            return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)
        
        # Extract code from URL if user pasted full URL
        auth_code = auth_input
        if "code=" in auth_input:
            try:
                if "example.com/callback" in auth_input or auth_input.startswith("http"):
                    code_part = auth_input.split("code=")[1]
                    auth_code = code_part.split("&")[0]
                    _LOG.info("Extracted code from URL. Original length: %d, Code length: %d", len(auth_input), len(auth_code))
                else:
                    auth_code = auth_input
                    _LOG.info("Using input as-is: %s", auth_code[:20] + "...")
            except Exception as e:
                _LOG.error("Failed to extract code from input: %s", e)
                return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)
        
        if not auth_code:
            _LOG.error("Could not extract authorization code from input.")
            return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)
        
        _LOG.info("Exchanging authorization code for access tokens...")
        try:
            success = await self._client.exchange_code_for_token(auth_code)
            
            if success:
                _LOG.info("Successfully authenticated with Spotify.")
                await self._setup_complete_callback()
                return ucapi.SetupComplete()
            else:
                _LOG.error("Failed to authenticate with Spotify.")
                return ucapi.SetupError(ucapi.IntegrationSetupError.AUTHORIZATION_ERROR)
                
        except Exception as e:
            _LOG.error("Error during token exchange: %s", e)
            return ucapi.SetupError(ucapi.IntegrationSetupError.OTHER)
    
    async def _handle_abort_setup(self, msg: ucapi.AbortDriverSetup) -> ucapi.SetupAction:
        _LOG.info("Setup aborted: %s", msg.error)
        self._config.clear_tokens()
        return ucapi.SetupError(msg.error)