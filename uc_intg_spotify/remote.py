"""Spotify remote entity. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from ucapi import remote, StatusCodes
from ucapi.ui import Buttons, Size, UiPage, create_btn_mapping, create_ui_icon, create_ui_text
from ucapi_framework import RemoteEntity

if TYPE_CHECKING:
    from uc_intg_spotify.config import SpotifyDeviceConfig
    from uc_intg_spotify.device import SpotifyDevice

_LOG = logging.getLogger(__name__)

SIMPLE_COMMANDS = [
    "PLAY_PAUSE",
    "PLAY",
    "PAUSE",
    "NEXT",
    "PREVIOUS",
    "VOLUME_UP",
    "VOLUME_DOWN",
    "MUTE_TOGGLE",
    "MUTE",
    "UNMUTE",
    "SHUFFLE",
    "REPEAT",
    "ADD_TO_QUEUE",
]


class SpotifyRemote(RemoteEntity):
    """Remote entity for Spotify."""

    def __init__(self, device_config: SpotifyDeviceConfig, device: SpotifyDevice) -> None:
        self._device = device

        entity_id = f"remote.{device_config.identifier}.remote"
        super().__init__(
            entity_id,
            "Spotify Remote",
            features=[remote.Features.SEND_CMD],
            attributes={remote.Attributes.STATE: remote.States.UNAVAILABLE},
            simple_commands=SIMPLE_COMMANDS,
            button_mapping=[
                create_btn_mapping(Buttons.PLAY, "PLAY_PAUSE"),
                create_btn_mapping(Buttons.NEXT, "NEXT"),
                create_btn_mapping(Buttons.PREV, "PREVIOUS"),
                create_btn_mapping(Buttons.VOLUME_UP, "VOLUME_UP"),
                create_btn_mapping(Buttons.VOLUME_DOWN, "VOLUME_DOWN"),
                create_btn_mapping(Buttons.MUTE, "MUTE_TOGGLE"),
            ],
            ui_pages=_create_ui_pages(),
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        has_client = self._device.client is not None and self._device.client.is_authenticated()
        state = remote.States.ON if has_client else remote.States.OFF
        self.update({remote.Attributes.STATE: state})

    async def _handle_command(
        self, entity: remote.Remote, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        client = self._device.client
        if not client or not client.is_authenticated():
            return StatusCodes.SERVICE_UNAVAILABLE

        try:
            if cmd_id == remote.Commands.SEND_CMD:
                return await self._handle_send_cmd(client, params)
            return StatusCodes.NOT_IMPLEMENTED
        except Exception as err:
            _LOG.error("Remote command %s failed: %s", cmd_id, err)
            return StatusCodes.SERVER_ERROR

    async def _handle_send_cmd(self, client, params: dict[str, Any] | None) -> StatusCodes:
        if not params or "command" not in params:
            return StatusCodes.BAD_REQUEST

        command = params["command"]
        ok = False

        if command == "PLAY_PAUSE":
            if self._device._is_playing:
                ok = await client.pause()
                is_playing = False
            else:
                device_id = self._device.get_first_available_device_id()
                ok = await client.play(device_id)
                is_playing = True
            if ok:
                self._device.set_playing_state(is_playing)
                self._device.schedule_playback_refresh()
        elif command == "PLAY":
            device_id = self._device.get_first_available_device_id() if not self._device._is_playing else None
            ok = await client.play(device_id)
            if ok:
                self._device.set_playing_state(True)
                self._device.schedule_playback_refresh()
        elif command == "PAUSE":
            ok = await client.pause()
            if ok:
                self._device.set_playing_state(False)
                self._device.schedule_playback_refresh()
        elif command == "NEXT":
            ok = await client.next_track()
            if ok:
                self._device.schedule_playback_refresh()
        elif command == "PREVIOUS":
            ok = await client.previous_track()
            if ok:
                self._device.schedule_playback_refresh()
        elif command == "VOLUME_UP":
            new_vol = min(100, self._device._volume + 1)
            ok = await client.set_volume(new_vol)
            if ok:
                self._device.set_volume_state(new_vol)
        elif command == "VOLUME_DOWN":
            new_vol = max(0, self._device._volume - 1)
            ok = await client.set_volume(new_vol)
            if ok:
                self._device.set_volume_state(new_vol)
        elif command == "MUTE_TOGGLE":
            volume = self._device.get_unmute_volume() if self._device._muted else 0
            ok = await client.set_volume(volume)
            if ok:
                self._device.set_volume_state(volume)
        elif command == "MUTE":
            ok = await client.set_volume(0)
            if ok:
                self._device.set_volume_state(0)
        elif command == "UNMUTE":
            volume = self._device.get_unmute_volume()
            ok = await client.set_volume(volume)
            if ok:
                self._device.set_volume_state(volume)
        elif command == "SHUFFLE":
            shuffle = not self._device._shuffle
            ok = await client.set_shuffle(shuffle)
            if ok:
                self._device.set_shuffle_state(shuffle)
                self._device.schedule_playback_refresh()
        elif command == "REPEAT":
            cycle = {"off": "context", "context": "track", "track": "off"}
            repeat = cycle.get(self._device._repeat, "off")
            ok = await client.set_repeat(repeat)
            if ok:
                self._device.set_repeat_state(repeat)
                self._device.schedule_playback_refresh()
        else:
            _LOG.warning("Unknown remote command: %s", command)
            return StatusCodes.NOT_IMPLEMENTED

        return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR


def _create_ui_pages() -> list[UiPage]:
    main = UiPage(page_id="main", name="Playback", grid=Size(4, 6))
    main.add(create_ui_icon("uc:backward", 0, 1, Size(2, 1), "PREVIOUS"))
    main.add(create_ui_icon("uc:forward", 2, 1, Size(2, 1), "NEXT"))
    main.add(create_ui_icon("uc:play-pause", 1, 2, Size(2, 2), "PLAY_PAUSE"))
    main.add(create_ui_text("Mute", 1, 0, Size(2, 1), "MUTE_TOGGLE"))
    main.add(create_ui_icon("uc:volume-high", 0, 4, Size(2, 1), "VOLUME_UP"))
    main.add(create_ui_icon("uc:volume-low", 2, 4, Size(2, 1), "VOLUME_DOWN"))
    main.add(create_ui_icon("uc:shuffle", 0, 5, Size(2, 1), "SHUFFLE"))
    main.add(create_ui_icon("uc:repeat", 2, 5, Size(2, 1), "REPEAT"))
    return [main]
