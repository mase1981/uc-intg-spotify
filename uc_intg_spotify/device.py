"""Spotify polling device. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import re
import time
from typing import Any

from ucapi import DeviceStates
from ucapi_framework import DeviceEvents, PollingDevice

from uc_intg_spotify.client import SpotifyAuthError, SpotifyClient
from uc_intg_spotify.config import SpotifyDeviceConfig
from uc_intg_spotify.discovery import SpotifyDiscovery, resolve_device_names, _is_junk_name

_LOG = logging.getLogger(__name__)

_HEX_HASH_RE = re.compile(r"^[0-9a-f]{32,}$", re.IGNORECASE)

DEVICE_CACHE_TTL = 86400  # 24 hours
PLAYBACK_REFRESH_DELAY = 0.5

_DEVICE_TYPE_LABELS = {
    "Computer": "Computer",
    "Smartphone": "Phone",
    "Tablet": "Tablet",
    "Speaker": "Speaker",
    "TV": "TV",
    "AVR": "Receiver",
    "STB": "Set-Top Box",
    "AudioDongle": "Audio Dongle",
    "GameConsole": "Game Console",
    "CastVideo": "Chromecast",
    "CastAudio": "Cast Audio",
    "Automobile": "Car",
}


def device_display_name(dev: dict[str, Any]) -> str:
    """Build a user-friendly display name for a Spotify Connect device."""
    override = dev.get("_display_name", "")
    if override:
        return override
    name = dev.get("name", "")
    if name and not _HEX_HASH_RE.match(name):
        return name
    dev_type = dev.get("type", "Device")
    label = _DEVICE_TYPE_LABELS.get(dev_type, dev_type)
    dev_id = dev.get("id", "")
    return f"{label} ({dev_id[:6]})" if dev_id else label


class SpotifyDevice(PollingDevice):
    """Spotify cloud device using polling for playback state updates."""

    def __init__(self, device_config: SpotifyDeviceConfig, **kwargs: Any) -> None:
        poll_interval = device_config.polling_interval or 10
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
        self._volume: int = 0
        self._muted: bool = False
        self._last_nonzero_volume: int = 50
        self._shuffle: bool = False
        self._smart_shuffle: bool = False
        self._repeat: str = "off"
        self._media_uri: str = ""
        self._context_uri: str = ""
        self._context_type: str = ""
        self._media_type: str = "track"

        self._source_name: str = ""
        self._source_list: list[str] = []
        self._devices: list[dict[str, Any]] = []
        self._disallows: dict[str, bool] = {}

        self._device_cache: dict[str, dict[str, Any]] = {}
        self._discovery = SpotifyDiscovery(on_update=self._on_zeroconf_update)
        self._playback_refresh_task: asyncio.Task[None] | None = None

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
            if device_display_name(dev) == name:
                return dev.get("id", "")
        for cached in self._device_cache.values():
            dev = cached["device"]
            if device_display_name(dev) == name:
                return dev.get("id", "")
        for zc_dev in self._discovery.devices.values():
            if zc_dev.get("name") == name:
                return zc_dev.get("device_id", "")
        return None

    def get_first_available_device_id(self) -> str | None:
        if self._devices:
            return self._devices[0].get("id")
        return None

    def get_device_volume(self, device_id: str) -> int | None:
        for dev in self._devices:
            if dev.get("id") == device_id and dev.get("supports_volume"):
                return dev.get("volume_percent")
        return None

    def set_playing_state(self, is_playing: bool) -> None:
        self._is_playing = is_playing
        if is_playing:
            self._state = "PLAYING"
        else:
            self._state = "PAUSED" if self._title else "ON"
        self.push_update()

    def set_volume_state(self, volume: int) -> None:
        self._volume = max(0, min(100, volume))
        self._muted = self._volume == 0
        if self._volume > 0:
            self._last_nonzero_volume = self._volume
        self.push_update()

    def get_unmute_volume(self) -> int:
        return max(1, min(100, self._last_nonzero_volume or 50))

    def set_shuffle_state(self, shuffle: bool) -> None:
        self._shuffle = shuffle
        if not shuffle:
            self._smart_shuffle = False
        self.push_update()

    def set_repeat_state(self, repeat: str) -> None:
        self._repeat = repeat if repeat in ("off", "context", "track") else "off"
        self.push_update()

    def schedule_playback_refresh(self) -> None:
        if self._playback_refresh_task and not self._playback_refresh_task.done():
            self._playback_refresh_task.cancel()
        self._playback_refresh_task = asyncio.create_task(self._refresh_playback_after_delay())

    async def _refresh_playback_after_delay(self) -> None:
        try:
            await asyncio.sleep(PLAYBACK_REFRESH_DELAY)
            await self.poll_device()
        except asyncio.CancelledError:
            raise
        except Exception as err:
            _LOG.debug("[%s] Playback refresh failed: %s", self.log_id, err)

    async def establish_connection(self) -> None:
        cfg = self._device_config
        self._client = SpotifyClient(cfg.access_token, cfg.refresh_token)
        self._client.set_credentials(cfg.client_id, cfg.client_secret)
        self._client.set_token_refresh_callback(self._persist_tokens)

        if not cfg.access_token or self._is_token_expired():
            try:
                token_data = await self._client.refresh_access_token()
            except SpotifyAuthError:
                await self._handle_auth_failure()
                raise ConnectionError("Spotify re-authentication required")
            if not token_data:
                raise ConnectionError("Failed to refresh Spotify access token")
            self._persist_tokens(token_data)

        self._discovery.start()
        self._state = "ON"
        _LOG.info("[%s] Connected to Spotify", self.log_id)

    async def poll_device(self) -> None:
        if not self._client:
            return

        try:
            playback = await self._client.get_playback_state()
            devices = await self._client.get_available_devices()

            if playback and playback.get("title"):
                self._is_playing = playback.get("is_playing", False)
                self._title = playback.get("title", "")
                self._artist = ", ".join(playback.get("artists", []))
                self._album = playback.get("album", "")
                self._image_url = playback.get("image_url", "")
                self._duration = playback.get("duration_ms", 0) // 1000
                self._position = playback.get("progress_ms", 0) // 1000
                self._volume = playback.get("volume_percent", 0)
                self._muted = self._volume == 0
                if self._volume > 0:
                    self._last_nonzero_volume = self._volume
                self._smart_shuffle = playback.get("smart_shuffle", False)
                self._shuffle = playback.get("shuffle_state", False) or self._smart_shuffle
                self._repeat = playback.get("repeat_state", "off")
                self._media_uri = playback.get("uri", "")
                self._media_type = playback.get("currently_playing_type", "track")
                self._disallows = playback.get("disallows", {})
                self._state = "PLAYING" if self._is_playing else "PAUSED"

                ctx = playback.get("context")
                if ctx:
                    self._context_uri = ctx.get("uri", "")
                    self._context_type = ctx.get("type", "")
                else:
                    self._context_uri = ""
                    self._context_type = ""

                active_id = playback.get("device_id", "")
                active_dev = next((d for d in devices if d.get("id") == active_id), None)
                if active_dev:
                    self._source_name = device_display_name(active_dev)
                else:
                    self._source_name = playback.get("device_name", "")
            elif playback:
                self._state = "ON"
                self._is_playing = False
                self._title = ""
                self._artist = ""
                self._album = ""
                self._image_url = ""
                self._duration = 0
                self._position = 0
                self._media_uri = ""
                self._volume = playback.get("volume_percent", 0)
                self._muted = self._volume == 0
                if self._volume > 0:
                    self._last_nonzero_volume = self._volume
                self._smart_shuffle = playback.get("smart_shuffle", False)
                self._shuffle = playback.get("shuffle_state", False) or self._smart_shuffle
                self._repeat = playback.get("repeat_state", "off")
                self._disallows = playback.get("disallows", {})
            else:
                self._state = "ON"
                self._is_playing = False
                self._title = ""
                self._artist = ""
                self._album = ""
                self._image_url = ""
                self._duration = 0
                self._position = 0
                self._media_uri = ""
                self._disallows = {}

            self._devices = devices
            self._update_device_cache(devices)
            await resolve_device_names(self._discovery)
            self._enrich_api_device_names()
            self._source_list = self._build_source_list(devices)

            self.push_update()

        except SpotifyAuthError:
            await self._handle_auth_failure()
        except Exception as err:
            _LOG.debug("[%s] Poll error: %s", self.log_id, err)
            if self._state != "UNAVAILABLE":
                self._state = "UNAVAILABLE"
                self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def _handle_auth_failure(self) -> None:
        """Discard the expired refresh token and flag that re-authentication is required."""
        _LOG.error(
            "[%s] Spotify refresh token rejected (invalid_grant). Re-authentication required: "
            "reconfigure the integration to sign in again.",
            self.log_id,
        )
        if self._client:
            self._client.set_tokens("", "")
        self.update_config(access_token="", refresh_token="", token_expires_at=0)
        self._state = "UNAVAILABLE"
        self.events.emit(DeviceEvents.ERROR, self.identifier, "Spotify re-authentication required")
        if self._driver is not None and getattr(self._driver, "api", None) is not None:
            try:
                await self._driver.api.set_device_state(DeviceStates.ERROR)
            except Exception as err:
                _LOG.debug("[%s] Could not set integration error state: %s", self.log_id, err)

    async def disconnect(self) -> None:
        if self._playback_refresh_task:
            self._playback_refresh_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._playback_refresh_task
            self._playback_refresh_task = None
        self._discovery.stop()
        if self._client:
            await self._client.close()
            self._client = None
        self._state = "UNAVAILABLE"
        await super().disconnect()

    def _update_device_cache(self, api_devices: list[dict[str, Any]]) -> None:
        now = time.time()
        for dev in api_devices:
            dev_id = dev.get("id", "")
            if dev_id:
                self._device_cache[dev_id] = {
                    "device": dev,
                    "last_seen": now,
                }

        expired = [k for k, v in self._device_cache.items() if now - v["last_seen"] > DEVICE_CACHE_TTL]
        for k in expired:
            del self._device_cache[k]

    def _build_source_list(self, api_devices: list[dict[str, Any]]) -> list[str]:
        seen_names: set[str] = set()
        result: list[str] = []

        for dev in api_devices:
            if dev.get("id"):
                name = device_display_name(dev)
                if name not in seen_names:
                    seen_names.add(name)
                    result.append(name)

        zeroconf_devices = self._discovery.devices
        for zc_dev in zeroconf_devices.values():
            name = zc_dev.get("name", "")
            if name and not _is_junk_name(name) and name not in seen_names:
                seen_names.add(name)
                result.append(name)

        for cached in self._device_cache.values():
            dev = cached["device"]
            name = device_display_name(dev)
            if name not in seen_names:
                seen_names.add(name)
                result.append(name)

        return result

    def _enrich_api_device_names(self) -> None:
        """Use Zeroconf-resolved names to fix API devices with hex hash names."""
        zc_by_id: dict[str, str] = {}
        for zc_dev in self._discovery.devices.values():
            device_id = zc_dev.get("device_id", "")
            name = zc_dev.get("name", "")
            if device_id and name:
                zc_by_id[device_id] = name

        for dev in self._devices:
            api_name = dev.get("name", "")
            api_id = dev.get("id", "")
            if api_id and api_name and _HEX_HASH_RE.match(api_name):
                resolved_name = zc_by_id.get(api_id, "")
                if resolved_name:
                    dev["_display_name"] = resolved_name

    def _on_zeroconf_update(self) -> None:
        if self._state != "UNAVAILABLE":
            self._source_list = self._build_source_list(self._devices)
            self.push_update()

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
