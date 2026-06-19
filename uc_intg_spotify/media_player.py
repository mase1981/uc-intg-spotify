"""Spotify media player entity. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from ucapi import media_player, StatusCodes
from ucapi.media_player import BrowseOptions, BrowseResults, SearchOptions, SearchResults
from ucapi_framework import MediaPlayerEntity

from uc_intg_spotify import browser
from uc_intg_spotify.config import account_suffix

if TYPE_CHECKING:
    from uc_intg_spotify.config import SpotifyDeviceConfig
    from uc_intg_spotify.device import SpotifyDevice

_LOG = logging.getLogger(__name__)


class SpotifyMediaPlayer(MediaPlayerEntity):
    """Media player entity for Spotify."""

    def __init__(self, device_config: SpotifyDeviceConfig, device: SpotifyDevice) -> None:
        self._device = device

        entity_id = f"media_player.{device_config.identifier}.player"
        super().__init__(
            entity_id,
            f"Spotify Player{account_suffix(device_config)}",
            features=[
                media_player.Features.ON_OFF,
                media_player.Features.PLAY_PAUSE,
                media_player.Features.NEXT,
                media_player.Features.PREVIOUS,
                media_player.Features.VOLUME,
                media_player.Features.VOLUME_UP_DOWN,
                media_player.Features.MUTE_TOGGLE,
                media_player.Features.MUTE,
                media_player.Features.UNMUTE,
                media_player.Features.SEEK,
                media_player.Features.SHUFFLE,
                media_player.Features.REPEAT,
                media_player.Features.MEDIA_DURATION,
                media_player.Features.MEDIA_POSITION,
                media_player.Features.MEDIA_TITLE,
                media_player.Features.MEDIA_ARTIST,
                media_player.Features.MEDIA_ALBUM,
                media_player.Features.MEDIA_IMAGE_URL,
                media_player.Features.MEDIA_TYPE,
                media_player.Features.PLAY_MEDIA,
                media_player.Features.BROWSE_MEDIA,
                media_player.Features.SEARCH_MEDIA,
                media_player.Features.SELECT_SOURCE,
            ],
            attributes={
                media_player.Attributes.STATE: media_player.States.UNAVAILABLE,
                media_player.Attributes.MEDIA_TYPE: "MUSIC",
            },
            device_class=media_player.DeviceClasses.SPEAKER,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        d = self._device
        state_map = {
            "PLAYING": media_player.States.PLAYING,
            "PAUSED": media_player.States.PAUSED,
            "ON": media_player.States.ON,
        }
        state = state_map.get(d._state, media_player.States.UNAVAILABLE)

        attrs: dict[str, Any] = {
            media_player.Attributes.STATE: state,
            media_player.Attributes.MEDIA_TYPE: "MUSIC",
        }

        if d._state in ("PLAYING", "PAUSED"):
            attrs.update({
                media_player.Attributes.VOLUME: d._volume,
                media_player.Attributes.MEDIA_TITLE: d._title,
                media_player.Attributes.MEDIA_ARTIST: d._artist,
                media_player.Attributes.MEDIA_ALBUM: d._album,
                media_player.Attributes.MEDIA_IMAGE_URL: d._image_url,
                media_player.Attributes.MEDIA_DURATION: d._duration,
                media_player.Attributes.MEDIA_POSITION: d._position,
                media_player.Attributes.MUTED: d._muted,
                media_player.Attributes.SHUFFLE: d._shuffle,
                media_player.Attributes.REPEAT: _repeat_to_uc(d._repeat),
                media_player.Attributes.SOURCE: d._source_name,
                media_player.Attributes.SOURCE_LIST: d._source_list,
            })
        elif d._state == "ON":
            attrs[media_player.Attributes.SOURCE_LIST] = d._source_list
            if d._source_name:
                attrs[media_player.Attributes.SOURCE] = d._source_name

        self.update(attrs)

    async def browse(self, options: BrowseOptions) -> BrowseResults | StatusCodes:
        client = self._device.client
        if not client or not client.is_authenticated():
            return StatusCodes.SERVICE_UNAVAILABLE
        return await browser.browse(client, options)

    async def search(self, options: SearchOptions) -> SearchResults | StatusCodes:
        client = self._device.client
        if not client or not client.is_authenticated():
            return StatusCodes.SERVICE_UNAVAILABLE
        return await browser.search(client, options)

    async def _handle_command(
        self, entity: media_player.MediaPlayer, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        client = self._device.client
        if not client or not client.is_authenticated():
            return StatusCodes.SERVICE_UNAVAILABLE

        try:
            return await self._dispatch_command(client, cmd_id, params)
        except Exception as err:
            _LOG.error("Command %s failed: %s", cmd_id, err)
            return StatusCodes.SERVER_ERROR

    async def _dispatch_command(self, client, cmd_id: str, params: dict[str, Any] | None) -> StatusCodes:
        if cmd_id == media_player.Commands.ON:
            return StatusCodes.OK

        if cmd_id == media_player.Commands.OFF:
            ok = await client.pause()
            if ok:
                self._device.set_playing_state(False)
                self._device.schedule_playback_refresh()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.PLAY_PAUSE:
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
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.NEXT:
            ok = await client.next_track()
            if ok:
                self._device.schedule_playback_refresh()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.PREVIOUS:
            ok = await client.previous_track()
            if ok:
                self._device.schedule_playback_refresh()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.VOLUME:
            volume = int(params.get("volume", 50)) if params else 50
            ok = await client.set_volume(volume)
            if ok:
                self._device.set_volume_state(volume)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.VOLUME_UP:
            new_vol = min(100, self._device._volume + 1)
            ok = await client.set_volume(new_vol)
            if ok:
                self._device.set_volume_state(new_vol)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.VOLUME_DOWN:
            new_vol = max(0, self._device._volume - 1)
            ok = await client.set_volume(new_vol)
            if ok:
                self._device.set_volume_state(new_vol)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.MUTE_TOGGLE:
            volume = self._device.get_unmute_volume() if self._device._muted else 0
            ok = await client.set_volume(volume)
            if ok:
                self._device.set_volume_state(volume)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.MUTE:
            ok = await client.set_volume(0)
            if ok:
                self._device.set_volume_state(0)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.UNMUTE:
            volume = self._device.get_unmute_volume()
            ok = await client.set_volume(volume)
            if ok:
                self._device.set_volume_state(volume)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.SEEK:
            position = params.get("media_position", 0) if params else 0
            ok = await client.seek(int(position) * 1000)
            if ok:
                self._device.schedule_playback_refresh()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.SHUFFLE:
            shuffle = _parse_shuffle_param(params, self._device._shuffle)
            ok = await client.set_shuffle(shuffle)
            if ok:
                self._device.set_shuffle_state(shuffle)
                self._device.schedule_playback_refresh()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.REPEAT:
            cycle = {"off": "context", "context": "track", "track": "off"}
            new_state = _parse_repeat_param(params, cycle.get(self._device._repeat, "off"))
            ok = await client.set_repeat(new_state)
            if ok:
                self._device.set_repeat_state(new_state)
                self._device.schedule_playback_refresh()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.SELECT_SOURCE:
            return await self._handle_select_source(client, params)

        if cmd_id == media_player.Commands.PLAY_MEDIA:
            return await self._handle_play_media(client, params)

        _LOG.warning("Unhandled command: %s", cmd_id)
        return StatusCodes.NOT_IMPLEMENTED

    async def _handle_select_source(self, client, params: dict[str, Any] | None) -> StatusCodes:
        if not params:
            return StatusCodes.BAD_REQUEST

        source = params.get("source", "")
        if not source:
            return StatusCodes.BAD_REQUEST

        device_id = self._device.get_device_id_by_name(source)
        if not device_id:
            _LOG.warning("Device not found: %s", source)
            return StatusCodes.BAD_REQUEST

        ok = await client.transfer_playback(device_id)
        return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

    async def _handle_play_media(self, client, params: dict[str, Any] | None) -> StatusCodes:
        if not params:
            return StatusCodes.BAD_REQUEST

        media_id = params.get("media_id", "")
        if not media_id:
            return StatusCodes.BAD_REQUEST

        uri = _media_id_to_uri(media_id)
        if not uri:
            _LOG.warning("Unknown media_id format: %s", media_id)
            return StatusCodes.BAD_REQUEST

        device_id = None
        target_volume = None
        if not self._device._is_playing:
            device_id = self._device.get_first_available_device_id()
            if device_id:
                target_volume = self._device.get_device_volume(device_id)

        ok = await client.play_uri(uri, device_id)
        if ok and device_id and target_volume is not None:
            await client.set_volume(target_volume, device_id)
        return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR


def _media_id_to_uri(media_id: str) -> str:
    prefixes = {
        "track_": "spotify:track:",
        "album_": "spotify:album:",
        "playlist_": "spotify:playlist:",
        "artist_": "spotify:artist:",
    }
    for prefix, uri_prefix in prefixes.items():
        if media_id.startswith(prefix):
            return f"{uri_prefix}{media_id[len(prefix):]}"
    return ""


def _parse_shuffle_param(params: dict[str, Any] | None, current: bool) -> bool:
    if not params or "shuffle" not in params:
        return not current
    value = params["shuffle"]
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("1", "true", "yes", "on")


def _parse_repeat_param(params: dict[str, Any] | None, default: str) -> str:
    if params:
        value = params.get("repeat")
        if value is not None:
            mapping = {
                "off": "off",
                "none": "off",
                "all": "context",
                "context": "context",
                "one": "track",
                "track": "track",
            }
            mapped = mapping.get(str(getattr(value, "value", value)).lower())
            if mapped:
                return mapped
    return default


def _repeat_to_uc(repeat: str) -> media_player.RepeatMode:
    mapping = {
        "off": media_player.RepeatMode.OFF,
        "context": media_player.RepeatMode.ALL,
        "track": media_player.RepeatMode.ONE,
    }
    return mapping.get(repeat, media_player.RepeatMode.OFF)
