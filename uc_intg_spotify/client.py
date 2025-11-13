"""
Spotify Web API client for Unfolded Circle integration.

:copyright: (c) 2024
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import base64
import logging
import ssl
from typing import Any, Dict, Optional

import aiohttp
import certifi

_LOG = logging.getLogger(__name__)

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"


class SpotifyClient:
    """Spotify Web API client with OAuth2 authentication."""
    
    def __init__(self, config):
        """Initialize the Spotify client."""
        self._config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._token_refresh_lock = asyncio.Lock()
        self.redirect_uri = "https://example.com/callback"
        
        _LOG.info("Spotify client initialized")
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with proper SSL context."""
        if self._session is None or self._session.closed:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'UC-Spotify-Integration/0.1.0'}
            )
        return self._session
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated with valid tokens."""
        access_token = self._config.get_access_token()
        refresh_token = self._config.get_refresh_token()
        return access_token is not None and refresh_token is not None
    
    def get_authorization_url(self) -> str:
        """Generate Spotify authorization URL for OAuth2 flow."""
        import urllib.parse
        
        client_id = self._config.get_client_id()
        if not client_id:
            raise ValueError("Client ID not configured")
        
        scopes = [
            "user-read-currently-playing",
            "user-read-playback-state",
            "user-modify-playback-state",
            "user-read-private"
        ]
        
        params = {
            "response_type": "code",
            "client_id": client_id,
            "scope": " ".join(scopes),
            "redirect_uri": self.redirect_uri,
            "show_dialog": "true"
        }
        
        return f"{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    async def exchange_code_for_token(self, authorization_code: str) -> bool:
        """Exchange authorization code for access and refresh tokens."""
        try:
            client_id = self._config.get_client_id()
            client_secret = self._config.get_client_secret()
            
            if not client_id or not client_secret:
                _LOG.error("Client ID or Client Secret not configured")
                return False
            
            session = await self._get_session()
            auth_header = base64.b64encode(
                f"{client_id}:{client_secret}".encode()
            ).decode()
            
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": self.redirect_uri
            }
            
            async with session.post(SPOTIFY_TOKEN_URL, headers=headers, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self._config.set_tokens(
                        token_data["access_token"],
                        token_data["refresh_token"],
                        token_data.get("expires_in", 3600)
                    )
                    _LOG.info("Successfully obtained Spotify access tokens")
                    return True
                else:
                    error_data = await response.text()
                    _LOG.error("Token exchange failed: %s - %s", response.status, error_data)
                    return False
                    
        except Exception as e:
            _LOG.error("Error exchanging authorization code for token: %s", e)
            return False
    
    async def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        async with self._token_refresh_lock:
            try:
                client_id = self._config.get_client_id()
                client_secret = self._config.get_client_secret()
                refresh_token = self._config.get_refresh_token()
                
                if not all([client_id, client_secret, refresh_token]):
                    _LOG.error("Missing credentials or refresh token")
                    return False
                
                session = await self._get_session()
                auth_header = base64.b64encode(
                    f"{client_id}:{client_secret}".encode()
                ).decode()
                
                headers = {
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
                
                async with session.post(SPOTIFY_TOKEN_URL, headers=headers, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        new_refresh_token = token_data.get("refresh_token", refresh_token)
                        self._config.set_tokens(
                            token_data["access_token"],
                            new_refresh_token,
                            token_data.get("expires_in", 3600)
                        )
                        _LOG.debug("Successfully refreshed Spotify access token")
                        return True
                    else:
                        error_data = await response.text()
                        _LOG.error("Token refresh failed: %s - %s", response.status, error_data)
                        return False
                        
            except Exception as e:
                _LOG.error("Error refreshing access token: %s", e)
                return False
    
    async def _make_authenticated_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make an authenticated request to the Spotify API."""
        if not self._config.get_access_token():
            _LOG.error("Not authenticated with Spotify")
            return None
        
        if self._config.is_token_expired():
            if not await self.refresh_access_token():
                _LOG.error("Failed to refresh access token")
                return None
        
        try:
            session = await self._get_session()
            access_token = self._config.get_access_token()
            
            headers = kwargs.get("headers", {})
            headers["Authorization"] = f"Bearer {access_token}"
            kwargs["headers"] = headers
            
            url = f"{SPOTIFY_API_BASE_URL}{endpoint}"
            
            async with session.request(method, url, **kwargs) as response:
                if 200 <= response.status < 300:
                    if response.status == 204:
                        return {}
                    
                    content_type = response.headers.get('Content-Type', '')
                    content_length = response.headers.get('Content-Length', '0')
                    
                    if content_length == '0' or 'application/json' not in content_type:
                        return {}
                    
                    try:
                        return await response.json()
                    except Exception:
                        return {}
                
                _LOG.error("API request failed: %s %s - Status: %s", method, url, response.status)
                return None
                
        except Exception as e:
            _LOG.error("Error making authenticated request: %s", e)
            return None
    
    async def get_currently_playing(self) -> Optional[Dict[str, Any]]:
        """Get the currently playing track from Spotify."""
        data = await self._make_authenticated_request("GET", "/me/player/currently-playing")
        
        if not data or not data.get("item"):
            return None
        
        track = data["item"]
        result = {
            "is_playing": data.get("is_playing", False),
            "title": track.get("name", "Unknown Title"),
            "artists": [artist["name"] for artist in track.get("artists", [])],
            "album": track.get("album", {}).get("name", "Unknown Album"),
            "duration_ms": track.get("duration_ms", 0),
            "progress_ms": data.get("progress_ms", 0),
            "image_url": None,
        }
        
        if track.get("album", {}).get("images"):
            result["image_url"] = track["album"]["images"][0]["url"]
        
        return result

    async def get_playback_state(self) -> Optional[Dict[str, Any]]:
        """Get current playback state including volume."""
        data = await self._make_authenticated_request("GET", "/me/player")
        if not data:
            return {}
        
        return {
            "is_playing": data.get("is_playing", False),
            "volume_percent": data.get("device", {}).get("volume_percent", 50),
            "device_name": data.get("device", {}).get("name", "Unknown"),
        }

    async def play_pause(self) -> bool:
        """Toggle play/pause state."""
        current_data = await self._make_authenticated_request("GET", "/me/player")
        if not current_data:
            return False
        
        is_playing = current_data.get("is_playing", False)
        endpoint = "/me/player/pause" if is_playing else "/me/player/play"
        result = await self._make_authenticated_request("PUT", endpoint)
        return result is not None
    
    async def play(self) -> bool:
        """Start playback."""
        result = await self._make_authenticated_request("PUT", "/me/player/play")
        return result is not None
    
    async def pause(self) -> bool:
        """Pause playback."""
        result = await self._make_authenticated_request("PUT", "/me/player/pause")
        return result is not None
    
    async def next_track(self) -> bool:
        """Skip to next track."""
        result = await self._make_authenticated_request("POST", "/me/player/next")
        return result is not None
    
    async def previous_track(self) -> bool:
        """Skip to previous track."""
        result = await self._make_authenticated_request("POST", "/me/player/previous")
        return result is not None

    async def set_volume(self, volume_percent: int) -> bool:
        """Set playback volume (0-100)."""
        volume_percent = max(0, min(100, volume_percent))
        result = await self._make_authenticated_request(
            "PUT", 
            f"/me/player/volume?volume_percent={volume_percent}"
        )
        return result is not None

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()