"""Spotify sensor entities. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from ucapi.sensor import Attributes, DeviceClasses, Sensor, States
from ucapi_framework import SensorEntity

if TYPE_CHECKING:
    from uc_intg_spotify.config import SpotifyDeviceConfig
    from uc_intg_spotify.device import SpotifyDevice

_LOG = logging.getLogger(__name__)


class SpotifyNowPlayingSensor(SensorEntity):
    """Sensor showing current track info as a single value."""

    def __init__(self, device_config: SpotifyDeviceConfig, device: SpotifyDevice) -> None:
        self._device = device

        entity_id = f"sensor.{device_config.identifier}.now_playing"

        super().__init__(
            entity_id,
            "Spotify Now Playing",
            [],
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.VALUE: "",
            },
            device_class=DeviceClasses.CUSTOM,
            options={"custom_unit": ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        d = self._device
        if d._state == "UNAVAILABLE":
            state = States.UNAVAILABLE
            value = "Unavailable"
        elif d._title:
            state = States.ON
            value = f"{d._title} - {d._artist}" if d._artist else d._title
        else:
            state = States.ON
            value = "Nothing playing"
        self.update({Attributes.STATE: state, Attributes.VALUE: value})


class SpotifyDeviceSensor(SensorEntity):
    """Sensor showing the active playback device."""

    def __init__(self, device_config: SpotifyDeviceConfig, device: SpotifyDevice) -> None:
        self._device = device

        entity_id = f"sensor.{device_config.identifier}.active_device"

        super().__init__(
            entity_id,
            "Spotify Active Device",
            [],
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.VALUE: "",
            },
            device_class=DeviceClasses.CUSTOM,
            options={"custom_unit": ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        d = self._device
        if d._state == "UNAVAILABLE":
            state = States.UNAVAILABLE
            value = "Unavailable"
        elif d._source_name:
            state = States.ON
            value = d._source_name
        else:
            state = States.ON
            value = "None"
        self.update({Attributes.STATE: state, Attributes.VALUE: value})
