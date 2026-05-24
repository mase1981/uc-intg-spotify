"""Spotify polling device. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
from __future__ import annotations

import logging
import re
import time
from typing import Any

from ucapi_framework import DeviceEvents, PollingDevice

from uc_intg_spotify.client import SpotifyClient
from uc_intg_spotify.config import SpotifyDeviceConfig

_LOG = logging.getLogger(__name__)

TRACK_END_SETTLE_SECONDS = 1.5
_HEX_HASH_RE = re.compile(r"^[0-9a-f]{32,}$", re.IGNORECASE)


def _device_display_name(dev: dict[str, Any]) -> str:
    name = dev.get("name", "")
    if name and not _HEX_HASH_RE.match(name):
        return name
    dev_type = dev.get("type", "Device")
    dev_id = dev.get("id", "")
    return f"{dev_type} ({dev_id[:8]})" if dev_id else dev_type


class SpotifyDevice(PollingDevice):
    """Spotify cloud device using polling for playback state updates."""

    def __init__(self, device_config: SpotifyDeviceConfig, **kwargs: Any) -> None:
        poll_interval = device_config.polling_interval or 30
        super().__init__(device_config, poll_interval=poll_interval, **kwargs)
        self._device_config: SpotifyDeviceConfig = device_config
        self._client: SpotifyClient | None = None
        self._state: str = "UNAVAILABLE"

        self._is_playing: bool = False
        self._title: str = ""
        self._artist: str = ""
        self._album: str = ""
        self._image_url: str = ""
        self._duration: int = 0
        self._position: int = 0
        self._volume: int = 50
        self._muted: bool = False
        self._shuffle: bool = False
        self._repeat: str = "off"
        self._media_uri: str = ""

        self._source_name: str = ""
        self._source_list: list[str] = []
        self._devices: list[dict[str, Any]] = []

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_config.name

    @property
    def address(self) -> str | None:
        return "api.spotify.com"

    @property
    def log_id(self) -> str:
        return f"Spotify ({self._device_config.name})"

    @property
    def client(self) -> SpotifyClient | None:
        return self._client

    def get_device_id_by_name(self, name: str) -> str | None:
        for dev in self._devices:
            if _device_display_name(dev) == name:
                return dev.get("id", "")
        return None

    def get_first_available_device_id(self) -> str | None:
        if self._devices:
            return self._devices[0].get("id")
        return None

    async def establish_connection(self) -> None:
        cfg = self._device_config
        self._client = SpotifyClient(cfg.access_token, cfg.refresh_token)
        self._client.set_credentials(cfg.client_id, cfg.client_secret)
        self._client.set_token_refresh_callback(self._persist_tokens)

        if not cfg.access_token or self._is_token_expired():
            token_data = await self._client.refresh_access_token()
            if not token_data:
                raise ConnectionError("Failed to refresh Spotify access token")
            self._persist_tokens(token_data)

        self._state = "ON"
        _LOG.info("[%s] Connected to Spotify", self.log_id)

    async def poll_device(self) -> None:
        if not self._client:
            return

        try:
            track_data = await self._client.get_currently_playing()
            playback = await self._client.get_playback_state()
            devices = await self._client.get_available_devices()

            if track_data:
                self._is_playing = track_data.get("is_playing", False)
                self._title = track_data.get("title", "")
                self._artist = ", ".join(track_data.get("artists", []))
                self._album = track_data.get("album", "")
                self._image_url = track_data.get("image_url", "")
                self._duration = track_data.get("duration_ms", 0) // 1000
                self._position = track_data.get("progress_ms", 0) // 1000
                self._media_uri = track_data.get("uri", "")
                self._state = "PLAYING" if self._is_playing else "PAUSED"
            else:
                self._state = "ON"
                self._title = ""
                self._artist = ""
                self._album = ""
                self._image_url = ""
                self._duration = 0
                self._position = 0
                self._media_uri = ""
                self._is_playing = False

            if playback:
                self._volume = playback.get("volume_percent", 50)
                self._muted = self._volume == 0
                self._shuffle = playback.get("shuffle_state", False)
                self._repeat = playback.get("repeat_state", "off")
                active_id = playback.get("device_id", "")
                active_dev = next((d for d in devices if d.get("id") == active_id), None)
                self._source_name = _device_display_name(active_dev) if active_dev else playback.get("device_name", "")

            self._devices = devices
            self._source_list = [_device_display_name(d) for d in devices if d.get("id")]

            self.push_update()

        except Exception as err:
            _LOG.debug("[%s] Poll error: %s", self.log_id, err)
            if self._state != "UNAVAILABLE":
                self._state = "UNAVAILABLE"
                self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
        self._state = "UNAVAILABLE"
        await super().disconnect()

    def _is_token_expired(self) -> bool:
        return int(time.time()) >= self._device_config.token_expires_at

    def _persist_tokens(self, token_data: dict[str, Any]) -> None:
        expires_in = token_data.get("expires_in", 3600)
        new_refresh = token_data.get("refresh_token", self._device_config.refresh_token)
        self.update_config(
            access_token=token_data["access_token"],
            refresh_token=new_refresh,
            token_expires_at=int(time.time()) + expires_in - 60,
        )
