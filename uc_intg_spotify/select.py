"""Spotify select entities. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from ucapi import StatusCodes
from ucapi.select import Attributes, Commands, Select, States
from ucapi_framework import SelectEntity

from uc_intg_spotify.config import account_suffix

if TYPE_CHECKING:
    from uc_intg_spotify.config import SpotifyDeviceConfig
    from uc_intg_spotify.device import SpotifyDevice

_LOG = logging.getLogger(__name__)


class SpotifyDeviceSelect(SelectEntity):
    """Select entity for choosing the active Spotify Connect device."""

    def __init__(self, device_config: SpotifyDeviceConfig, device: SpotifyDevice) -> None:
        self._device = device

        entity_id = f"select.{device_config.identifier}.active_device"

        super().__init__(
            entity_id,
            f"Spotify Active Device{account_suffix(device_config)}",
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.OPTIONS: [],
                Attributes.CURRENT_OPTION: "",
            },
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        d = self._device
        state = States.ON if d._state != "UNAVAILABLE" else States.UNAVAILABLE
        self.update({
            Attributes.STATE: state,
            Attributes.OPTIONS: d._source_list,
            Attributes.CURRENT_OPTION: d._source_name,
        })

    async def _handle_command(
        self, entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        client = self._device.client
        if not client or not client.is_authenticated():
            return StatusCodes.SERVICE_UNAVAILABLE

        if cmd_id == Commands.SELECT_OPTION:
            option = params.get("option", "") if params else ""
            if not option:
                return StatusCodes.BAD_REQUEST

            device_id = self._device.get_device_id_by_name(option)
            if not device_id:
                _LOG.warning("Device not found for option: %s", option)
                return StatusCodes.BAD_REQUEST

            ok = await client.transfer_playback(device_id)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == Commands.SELECT_NEXT:
            return await self._select_adjacent(1)

        if cmd_id == Commands.SELECT_PREVIOUS:
            return await self._select_adjacent(-1)

        return StatusCodes.NOT_IMPLEMENTED

    async def _select_adjacent(self, direction: int) -> StatusCodes:
        client = self._device.client
        if not client or not client.is_authenticated():
            return StatusCodes.SERVICE_UNAVAILABLE

        options = self._device._source_list
        if not options:
            return StatusCodes.BAD_REQUEST

        current = self._device._source_name
        try:
            idx = options.index(current)
        except ValueError:
            idx = 0

        new_idx = (idx + direction) % len(options)
        new_option = options[new_idx]

        device_id = self._device.get_device_id_by_name(new_option)
        if not device_id:
            return StatusCodes.BAD_REQUEST

        ok = await client.transfer_playback(device_id)
        return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
