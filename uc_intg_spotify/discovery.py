"""Spotify Connect device discovery via Zeroconf/mDNS."""
from __future__ import annotations

import logging
import re
import threading
from typing import Any, Callable

import aiohttp

from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf

_LOG = logging.getLogger(__name__)

SPOTIFY_CONNECT_SERVICE = "_spotify-connect._tcp.local."

_HEX_HASH_RE = re.compile(r"^[0-9a-f]{12,}$", re.IGNORECASE)
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-", re.IGNORECASE)


def _is_junk_name(name: str) -> bool:
    if not name:
        return True
    if _HEX_HASH_RE.match(name):
        return True
    if _UUID_RE.match(name):
        return True
    if name.startswith("SpZc-"):
        return True
    return False


class SpotifyDiscovery:
    """Discovers Spotify Connect devices on the local network via mDNS."""

    def __init__(self, on_update: Callable[[], None] | None = None) -> None:
        self._zeroconf: Zeroconf | None = None
        self._browser: ServiceBrowser | None = None
        self._devices: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._on_update = on_update

    @property
    def devices(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return dict(self._devices)

    def start(self) -> None:
        if self._zeroconf:
            return
        try:
            self._zeroconf = Zeroconf()
            self._browser = ServiceBrowser(
                self._zeroconf,
                SPOTIFY_CONNECT_SERVICE,
                handlers=[self._on_state_change],
            )
            _LOG.info("Spotify Connect Zeroconf discovery started")
        except Exception as err:
            _LOG.warning("Failed to start Zeroconf discovery: %s", err)
            self._zeroconf = None
            self._browser = None

    def stop(self) -> None:
        if self._browser:
            self._browser.cancel()
            self._browser = None
        if self._zeroconf:
            self._zeroconf.close()
            self._zeroconf = None
        with self._lock:
            self._devices.clear()
        _LOG.info("Spotify Connect Zeroconf discovery stopped")

    def _on_state_change(
        self, zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange
    ) -> None:
        if state_change in (ServiceStateChange.Added, ServiceStateChange.Updated):
            self._handle_service_found(zeroconf, service_type, name)
        elif state_change == ServiceStateChange.Removed:
            self._handle_service_removed(name)

    def _handle_service_found(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        try:
            info = zeroconf.get_service_info(service_type, name)
            if not info:
                return

            props = {}
            for k, v in info.properties.items():
                key = k.decode("utf-8", errors="replace") if isinstance(k, bytes) else str(k)
                val = v.decode("utf-8", errors="replace") if isinstance(v, bytes) else str(v)
                props[key] = val

            addresses = info.parsed_scoped_addresses()
            ip = addresses[0] if addresses else None
            port = info.port
            cpath = props.get("CPath", "/zc")

            if not ip or not port:
                _LOG.debug("Zeroconf: no address for %s, skipping", name)
                return

            with self._lock:
                self._devices[name] = {
                    "name": "",
                    "ip": ip,
                    "port": port,
                    "cpath": cpath,
                    "service_name": name,
                    "resolved": False,
                    "source": "zeroconf",
                }

            _LOG.debug(
                "Zeroconf: discovered service '%s' at %s:%s%s (props: %s)",
                name, ip, port, cpath, props,
            )

            if self._on_update:
                self._on_update()

        except Exception as err:
            _LOG.debug("Zeroconf: error resolving %s: %s", name, err)

    def _handle_service_removed(self, name: str) -> None:
        with self._lock:
            removed = self._devices.pop(name, None)
        if removed:
            _LOG.debug("Zeroconf: device removed '%s' (%s)", removed.get("name"), name)
            if self._on_update:
                self._on_update()


async def resolve_device_names(discovery: SpotifyDiscovery) -> None:
    """Query each discovered device's getInfo endpoint to resolve friendly names."""
    devices = discovery.devices
    for service_name, dev in devices.items():
        if dev.get("resolved"):
            continue

        ip = dev.get("ip")
        port = dev.get("port")
        cpath = dev.get("cpath", "/zc")

        if not ip or not port:
            continue

        result = await _query_device_info(ip, port, cpath)
        if result:
            friendly_name = result.get("name", "")
            device_id = result.get("device_id", "")
            with discovery._lock:
                if service_name in discovery._devices:
                    if friendly_name and not _is_junk_name(friendly_name):
                        discovery._devices[service_name]["name"] = friendly_name
                    discovery._devices[service_name]["device_id"] = device_id
                    discovery._devices[service_name]["resolved"] = True
            _LOG.debug("Zeroconf: resolved '%s' -> name='%s' id='%s'", service_name, friendly_name, device_id)
        else:
            with discovery._lock:
                if service_name in discovery._devices:
                    discovery._devices[service_name]["resolved"] = True
            _LOG.debug("Zeroconf: could not resolve info for %s", service_name)


async def _query_device_info(ip: str, port: int, cpath: str) -> dict[str, str] | None:
    """Query a Spotify Connect device's getInfo endpoint."""
    url = f"http://{ip}:{port}{cpath}?action=getInfo&version=2.7.1"
    try:
        timeout = aiohttp.ClientTimeout(total=4)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    device_id = data.get("deviceId", "")
                    remote_name = data.get("remoteName", "")
                    if not remote_name or _is_junk_name(remote_name):
                        aliases = data.get("aliases", [])
                        if aliases:
                            alias = aliases[0] if isinstance(aliases[0], str) else aliases[0].get("name", "")
                            if alias and not _is_junk_name(alias):
                                remote_name = alias
                    return {"name": remote_name, "device_id": device_id}
    except Exception as err:
        _LOG.debug("Zeroconf: getInfo query failed for %s:%s: %s", ip, port, err)
    return None
