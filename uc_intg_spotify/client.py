"""Spotify Web API client. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
from __future__ import annotations

import base64
import logging
import ssl
import urllib.parse
from typing import Any

import aiohttp
import certifi

_LOG = logging.getLogger(__name__)

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

REDIRECT_URI = "https://example.com/callback"

SCOPES = [
    "user-read-currently-playing",
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-private",
    "user-library-read",
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-top-read",
    "user-read-recently-played",
    "user-follow-read",
]


class SpotifyClient:
    """Spotify Web API client with OAuth2 authentication."""

    def __init__(self, access_token: str = "", refresh_token: str = "") -> None:
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._client_id = ""
        self._client_secret = ""
        self._session: aiohttp.ClientSession | None = None
        self._on_token_refresh: Any = None

    def set_credentials(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    def set_tokens(self, access_token: str, refresh_token: str) -> None:
        self._access_token = access_token
        self._refresh_token = refresh_token

    def set_token_refresh_callback(self, callback: Any) -> None:
        self._on_token_refresh = callback

    def is_authenticated(self) -> bool:
        return bool(self._access_token and self._refresh_token)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "UC-Spotify-Integration/2.1.0"},
            )
        return self._session

    def get_authorization_url(self, client_id: str) -> str:
        params = {
            "response_type": "code",
            "client_id": client_id,
            "scope": " ".join(SCOPES),
            "redirect_uri": REDIRECT_URI,
            "show_dialog": "true",
        }
        return f"{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code_for_token(
        self, authorization_code: str, client_id: str, client_secret: str
    ) -> dict[str, Any] | None:
        try:
            session = await self._get_session()
            auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

            async with session.post(
                SPOTIFY_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": REDIRECT_URI,
                },
            ) as response:
                if response.status == 200:
                    return await response.json()
                error = await response.text()
                _LOG.error("Token exchange failed: %s - %s", response.status, error)
                return None
        except Exception as e:
            _LOG.error("Error exchanging code: %s", e)
            return None

    async def refresh_access_token(self) -> dict[str, Any] | None:
        if not self._client_id or not self._client_secret or not self._refresh_token:
            _LOG.error("Missing credentials for token refresh")
            return None

        try:
            session = await self._get_session()
            auth_header = base64.b64encode(
                f"{self._client_id}:{self._client_secret}".encode()
            ).decode()

            async with session.post(
                SPOTIFY_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                },
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self._access_token = token_data["access_token"]
                    if "refresh_token" in token_data:
                        self._refresh_token = token_data["refresh_token"]
                    _LOG.debug("Token refreshed successfully")
                    if self._on_token_refresh:
                        self._on_token_refresh(token_data)
                    return token_data
                error = await response.text()
                _LOG.error("Token refresh failed: %s - %s", response.status, error)
                return None
        except Exception as e:
            _LOG.error("Error refreshing token: %s", e)
            return None

    async def _api_request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> dict[str, Any] | None:
        if not self._access_token:
            _LOG.error("Not authenticated")
            return None

        try:
            session = await self._get_session()
            headers = kwargs.pop("headers", {})
            headers["Authorization"] = f"Bearer {self._access_token}"

            url = f"{SPOTIFY_API_BASE_URL}{endpoint}"

            async with session.request(method, url, headers=headers, **kwargs) as response:
                if response.status == 401:
                    token_data = await self.refresh_access_token()
                    if not token_data:
                        return None
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with session.request(method, url, headers=headers, **kwargs) as retry:
                        if 200 <= retry.status < 300:
                            return {} if retry.status == 204 else await retry.json()
                        return None

                if 200 <= response.status < 300:
                    if response.status == 204:
                        return {}
                    try:
                        return await response.json()
                    except (aiohttp.ContentTypeError, ValueError):
                        return {}

                body = await response.text()
                _LOG.error("API %s %s failed: %s - %s", method, endpoint, response.status, body[:500])
                return None
        except Exception as e:
            _LOG.error("API request error: %s", e)
            return None

    # ── Playback ──

    async def get_currently_playing(self) -> dict[str, Any] | None:
        data = await self._api_request("GET", "/me/player/currently-playing")
        if not data or not data.get("item"):
            return None

        track = data["item"]
        return {
            "is_playing": data.get("is_playing", False),
            "title": track.get("name", "Unknown"),
            "artists": [a["name"] for a in track.get("artists", [])],
            "album": track.get("album", {}).get("name", ""),
            "duration_ms": track.get("duration_ms", 0),
            "progress_ms": data.get("progress_ms", 0),
            "image_url": (track.get("album", {}).get("images", [{}])[0].get("url", "")
                          if track.get("album", {}).get("images") else ""),
            "uri": track.get("uri", ""),
        }

    async def get_playback_state(self) -> dict[str, Any] | None:
        data = await self._api_request("GET", "/me/player")
        if not data:
            return None

        device = data.get("device", {})
        return {
            "is_playing": data.get("is_playing", False),
            "volume_percent": device.get("volume_percent", 50),
            "device_name": device.get("name", "Unknown"),
            "device_id": device.get("id", ""),
            "supports_volume": device.get("supports_volume", False),
            "shuffle_state": data.get("shuffle_state", False),
            "repeat_state": data.get("repeat_state", "off"),
        }

    async def play(self) -> bool:
        return await self._api_request("PUT", "/me/player/play") is not None

    async def pause(self) -> bool:
        return await self._api_request("PUT", "/me/player/pause") is not None

    async def play_pause(self) -> bool:
        state = await self._api_request("GET", "/me/player")
        if not state:
            return False
        endpoint = "/me/player/pause" if state.get("is_playing") else "/me/player/play"
        return await self._api_request("PUT", endpoint) is not None

    async def next_track(self) -> bool:
        return await self._api_request("POST", "/me/player/next") is not None

    async def previous_track(self) -> bool:
        return await self._api_request("POST", "/me/player/previous") is not None

    async def set_volume(self, volume_percent: int) -> bool:
        volume_percent = max(0, min(100, volume_percent))
        return await self._api_request(
            "PUT", f"/me/player/volume?volume_percent={volume_percent}"
        ) is not None

    async def seek(self, position_ms: int) -> bool:
        return await self._api_request(
            "PUT", f"/me/player/seek?position_ms={position_ms}"
        ) is not None

    async def set_shuffle(self, state: bool) -> bool:
        return await self._api_request(
            "PUT", f"/me/player/shuffle?state={'true' if state else 'false'}"
        ) is not None

    async def set_repeat(self, state: str) -> bool:
        return await self._api_request(
            "PUT", f"/me/player/repeat?state={state}"
        ) is not None

    async def play_uri(self, uri: str, device_id: str | None = None) -> bool:
        if uri.startswith("spotify:track:"):
            body: dict[str, Any] = {"uris": [uri]}
        else:
            body = {"context_uri": uri}

        endpoint = "/me/player/play"
        if device_id:
            endpoint = f"/me/player/play?device_id={device_id}"

        return await self._api_request("PUT", endpoint, json=body) is not None

    async def transfer_playback(self, device_id: str) -> bool:
        return await self._api_request(
            "PUT", "/me/player", json={"device_ids": [device_id], "play": False}
        ) is not None

    async def get_available_devices(self) -> list[dict[str, Any]]:
        data = await self._api_request("GET", "/me/player/devices")
        if data and "devices" in data:
            return data["devices"]
        return []

    # ── Browse / Library ──

    async def get_user_playlists(
        self, limit: int = 50, offset: int = 0
    ) -> dict[str, Any] | None:
        return await self._api_request(
            "GET", f"/me/playlists?limit={limit}&offset={offset}"
        )

    async def get_playlist(self, playlist_id: str) -> dict[str, Any] | None:
        return await self._api_request("GET", f"/playlists/{playlist_id}")

    async def get_saved_tracks(
        self, limit: int = 50, offset: int = 0
    ) -> dict[str, Any] | None:
        return await self._api_request(
            "GET", f"/me/tracks?limit={limit}&offset={offset}"
        )

    async def get_saved_albums(
        self, limit: int = 50, offset: int = 0
    ) -> dict[str, Any] | None:
        return await self._api_request(
            "GET", f"/me/albums?limit={limit}&offset={offset}"
        )

    async def get_album(self, album_id: str) -> dict[str, Any] | None:
        return await self._api_request("GET", f"/albums/{album_id}")

    async def get_artist(self, artist_id: str) -> dict[str, Any] | None:
        return await self._api_request("GET", f"/artists/{artist_id}")

    async def get_artist_top_tracks(self, artist_id: str) -> dict[str, Any] | None:
        return await self._api_request("GET", f"/artists/{artist_id}/top-tracks")

    async def get_artist_albums(
        self, artist_id: str, limit: int = 20, offset: int = 0
    ) -> dict[str, Any] | None:
        return await self._api_request(
            "GET",
            f"/artists/{artist_id}/albums?include_groups=album,single&limit={limit}&offset={offset}",
        )

    async def get_recently_played(
        self, limit: int = 50
    ) -> dict[str, Any] | None:
        return await self._api_request(
            "GET", f"/me/player/recently-played?limit={limit}"
        )

    async def get_top_artists(
        self, limit: int = 50, offset: int = 0
    ) -> dict[str, Any] | None:
        return await self._api_request(
            "GET", f"/me/top/artists?limit={limit}&offset={offset}"
        )

    async def get_top_tracks(
        self, limit: int = 50, offset: int = 0
    ) -> dict[str, Any] | None:
        return await self._api_request(
            "GET", f"/me/top/tracks?limit={limit}&offset={offset}"
        )

    async def get_followed_artists(
        self, limit: int = 50
    ) -> dict[str, Any] | None:
        return await self._api_request(
            "GET", f"/me/following?type=artist&limit={limit}"
        )

    async def search(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> dict[str, Any] | None:
        encoded = urllib.parse.quote(query)
        return await self._api_request(
            "GET",
            f"/search?q={encoded}&type=track,album,artist,playlist&limit={limit}&offset={offset}",
        )

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
