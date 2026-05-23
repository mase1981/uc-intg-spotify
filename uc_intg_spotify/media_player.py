"""Spotify media player entity. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from ucapi import media_player, StatusCodes
from ucapi.media_player import BrowseOptions, BrowseResults, SearchOptions, SearchResults
from ucapi_framework import MediaPlayerEntity

from uc_intg_spotify import browser

if TYPE_CHECKING:
    from uc_intg_spotify.config import SpotifyDeviceConfig
    from uc_intg_spotify.device import SpotifyDevice

_LOG = logging.getLogger(__name__)

FEATURES = [
    media_player.Features.ON_OFF,
    media_player.Features.PLAY_PAUSE,
    media_player.Features.NEXT,
    media_player.Features.PREVIOUS,
    media_player.Features.VOLUME,
    media_player.Features.VOLUME_UP_DOWN,
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
]


class SpotifyMediaPlayer(MediaPlayerEntity):
    """Media player entity for Spotify."""

    def __init__(self, device_config: SpotifyDeviceConfig, device: SpotifyDevice) -> None:
        self._device = device

        entity_id = f"media_player.{device_config.identifier}.player"
        super().__init__(
            entity_id,
            "Spotify Player",
            features=FEATURES,
            attributes={
                media_player.Attributes.STATE: media_player.States.UNAVAILABLE,
                media_player.Attributes.VOLUME: 50,
                media_player.Attributes.MUTED: False,
                media_player.Attributes.MEDIA_TITLE: "",
                media_player.Attributes.MEDIA_ARTIST: "",
                media_player.Attributes.MEDIA_ALBUM: "",
                media_player.Attributes.MEDIA_IMAGE_URL: "",
                media_player.Attributes.MEDIA_TYPE: "",
                media_player.Attributes.MEDIA_DURATION: 0,
                media_player.Attributes.MEDIA_POSITION: 0,
                media_player.Attributes.SHUFFLE: False,
                media_player.Attributes.REPEAT: media_player.RepeatMode.OFF,
            },
            device_class=media_player.DeviceClasses.SPEAKER,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        dev = self._device
        state = self.map_entity_states(dev._state)

        repeat_map = {"track": media_player.RepeatMode.ONE, "context": media_player.RepeatMode.ALL}
        repeat = repeat_map.get(dev._repeat, media_player.RepeatMode.OFF)

        self.update({
            media_player.Attributes.STATE: state,
            media_player.Attributes.VOLUME: dev._volume,
            media_player.Attributes.MUTED: dev._muted,
            media_player.Attributes.MEDIA_TITLE: dev._title,
            media_player.Attributes.MEDIA_ARTIST: dev._artist,
            media_player.Attributes.MEDIA_ALBUM: dev._album,
            media_player.Attributes.MEDIA_IMAGE_URL: dev._image_url,
            media_player.Attributes.MEDIA_TYPE: media_player.MediaContentType.MUSIC,
            media_player.Attributes.MEDIA_DURATION: dev._duration,
            media_player.Attributes.MEDIA_POSITION: dev._position,
            media_player.Attributes.SHUFFLE: dev._shuffle,
            media_player.Attributes.REPEAT: repeat,
        })

    async def browse(self, options: BrowseOptions) -> BrowseResults | StatusCodes:
        return await browser.browse(self._device.client, options)

    async def search(self, options: SearchOptions) -> SearchResults | StatusCodes:
        return await browser.search(self._device.client, options)

    async def _handle_command(
        self, entity: media_player.MediaPlayer, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        client = self._device.client
        if not client or not client.is_authenticated():
            return StatusCodes.SERVICE_UNAVAILABLE

        try:
            return await self._dispatch(client, cmd_id, params)
        except Exception as err:
            _LOG.error("Command %s failed: %s", cmd_id, err)
            return StatusCodes.SERVER_ERROR

    async def _dispatch(self, client, cmd_id: str, params: dict[str, Any] | None) -> StatusCodes:
        if cmd_id == media_player.Commands.ON:
            ok = await client.play()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.OFF:
            ok = await client.pause()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.PLAY_PAUSE:
            ok = await client.play_pause()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.NEXT:
            ok = await client.next_track()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.PREVIOUS:
            ok = await client.previous_track()
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.VOLUME and params:
            ok = await client.set_volume(params.get("volume", 50))
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.VOLUME_UP:
            new_vol = min(100, self._device._volume + 5)
            ok = await client.set_volume(new_vol)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.VOLUME_DOWN:
            new_vol = max(0, self._device._volume - 5)
            ok = await client.set_volume(new_vol)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.SEEK and params:
            position_s = params.get("media_position", 0)
            ok = await client.seek(int(position_s) * 1000)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.SHUFFLE:
            new_state = not self._device._shuffle
            ok = await client.set_shuffle(new_state)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.REPEAT:
            cycle = {"off": "context", "context": "track", "track": "off"}
            new_state = cycle.get(self._device._repeat, "off")
            ok = await client.set_repeat(new_state)
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR

        if cmd_id == media_player.Commands.PLAY_MEDIA:
            return await self._handle_play_media(client, params)

        _LOG.warning("Unhandled command: %s", cmd_id)
        return StatusCodes.NOT_IMPLEMENTED

    async def _handle_play_media(self, client, params: dict[str, Any] | None) -> StatusCodes:
        if not params:
            return StatusCodes.BAD_REQUEST

        media_id = params.get("media_id", "")
        if not media_id:
            return StatusCodes.BAD_REQUEST

        uri = ""
        if media_id.startswith("track_"):
            uri = f"spotify:track:{media_id[6:]}"
        elif media_id.startswith("album_"):
            uri = f"spotify:album:{media_id[6:]}"
        elif media_id.startswith("playlist_"):
            uri = f"spotify:playlist:{media_id[9:]}"
        elif media_id.startswith("artist_"):
            uri = f"spotify:artist:{media_id[7:]}"

        if not uri:
            _LOG.warning("Unknown media_id format: %s", media_id)
            return StatusCodes.BAD_REQUEST

        ok = await client.play_uri(uri)
        return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
