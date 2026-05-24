"""Spotify integration driver. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
from ucapi_framework import BaseIntegrationDriver

from uc_intg_spotify.config import SpotifyDeviceConfig
from uc_intg_spotify.device import SpotifyDevice
from uc_intg_spotify.media_player import SpotifyMediaPlayer
from uc_intg_spotify.remote import SpotifyRemote
from uc_intg_spotify.select import SpotifyDeviceSelect
from uc_intg_spotify.sensor import SpotifyNowPlayingSensor, SpotifyDeviceSensor


class SpotifyDriver(BaseIntegrationDriver[SpotifyDevice, SpotifyDeviceConfig]):
    """Spotify integration driver."""

    def __init__(self) -> None:
        super().__init__(
            device_class=SpotifyDevice,
            entity_classes=[
                SpotifyMediaPlayer,
                SpotifyRemote,
                SpotifyDeviceSelect,
                SpotifyNowPlayingSensor,
                SpotifyDeviceSensor,
            ],
            driver_id="spotify",
            require_connection_before_registry=True,
        )
