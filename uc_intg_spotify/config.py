"""Spotify configuration. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
from dataclasses import dataclass, field


@dataclass
class SpotifyDeviceConfig:
    """Spotify device configuration stored by the framework."""

    identifier: str
    name: str
    client_id: str
    client_secret: str
    access_token: str = ""
    refresh_token: str = ""
    token_expires_at: int = 0
    polling_interval: int = 10
