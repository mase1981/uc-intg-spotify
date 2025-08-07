"""
Spotify media player entity for Unfolded Circle integration.

:copyright: (c) 2024
:license: MPL-2.0, see LICENSE for more details.
"""
import asyncio
import logging
from typing import Any, Dict, Optional

import ucapi
from ucapi.media_player import Attributes, Commands, Features, States

from uc_intg_spotify.client import SpotifyClient
from uc_intg_spotify.config import SpotifyConfig

_LOG = logging.getLogger(__name__)


class SpotifyMediaPlayer:
    """Spotify media player entity."""
    
    def __init__(self, api: ucapi.IntegrationAPI, client: SpotifyClient):
        """Initialize Spotify media player."""
        self._api = api
        self._client = client
        self._config: SpotifyConfig = client._config if client else None
        self._polling_task: Optional[asyncio.Task] = None
        
        # Base features for all users
        features = [
            Features.ON_OFF,
            Features.MEDIA_DURATION,
            Features.MEDIA_POSITION,
            Features.MEDIA_TITLE,
            Features.MEDIA_ARTIST,
            Features.MEDIA_ALBUM,
            Features.MEDIA_IMAGE_URL,
            Features.MEDIA_TYPE
        ]
        
        # Add control features for Premium users
        if self._config and self._config.is_premium_user():
            _LOG.info("User has Spotify Premium - enabling playback controls")
            features.extend([
                Features.PLAY_PAUSE,
                Features.NEXT,
                Features.PREVIOUS,
                Features.VOLUME,
                Features.VOLUME_UP_DOWN,
            ])
        else:
            _LOG.info("User has Spotify Free - display only mode")
        
        attributes = {
            Attributes.STATE: States.OFF,
            Attributes.MEDIA_TITLE: "",
            Attributes.MEDIA_ARTIST: "",
            Attributes.MEDIA_ALBUM: "",
            Attributes.MEDIA_DURATION: 0,
            Attributes.MEDIA_POSITION: 0,
            Attributes.MEDIA_IMAGE_URL: "",
            Attributes.VOLUME: 50,
            Attributes.MUTED: False,
        }
        
        self.entity = ucapi.MediaPlayer(
            identifier="spotify_media_player_main",
            name={"en": "Spotify Player"},
            features=features,
            attributes=attributes,
            cmd_handler=self.cmd_handler
        )
        
        _LOG.info("Spotify media player entity created with %d features", len(features))

    async def start_polling(self):
        """Start the background polling task."""
        if not self._polling_task or self._polling_task.done():
            polling_interval = self._config.get_polling_interval()
            self._polling_task = asyncio.create_task(self._poll_playback_state(polling_interval))
            _LOG.info(f"Started polling Spotify every {polling_interval} seconds.")

    async def stop_polling(self):
        """Stop the background polling task."""
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            _LOG.info("Stopped polling Spotify.")
        self._polling_task = None
        
    async def _poll_playback_state(self, interval_seconds: int):
        """Periodically poll for playback state."""
        while True:
            try:
                if self._client.is_authenticated():
                    track_data = await self._client.get_currently_playing()
                    if track_data:
                        await self.update_current_track(track_data)
                    else:
                        await self.clear_current_track()
                else:
                    _LOG.debug("Polling skipped: client not authenticated.")
            except Exception as e:
                _LOG.error(f"Error during polling: {e}", exc_info=True)
            
            await asyncio.sleep(interval_seconds)

    async def cmd_handler(self, entity: ucapi.Entity, cmd_id: str, params: dict[str, Any] | None) -> ucapi.StatusCodes:
        """Handle media player commands."""
        _LOG.info("Media player command: %s %s", cmd_id, params)
        
        if not self._client or not self._client.is_authenticated():
            _LOG.warning("Spotify client not authenticated")
            return ucapi.StatusCodes.SERVICE_UNAVAILABLE
        
        try:
            # Handle ON/OFF commands for all users
            if cmd_id == Commands.ON:
                return await self._handle_on()
            elif cmd_id == Commands.OFF:
                return await self._handle_off()
            
            # Check Premium status for control commands
            if not self._config.is_premium_user():
                premium_commands = [
                    Commands.PLAY_PAUSE, Commands.NEXT, Commands.PREVIOUS,
                    Commands.VOLUME, Commands.VOLUME_UP, Commands.VOLUME_DOWN,
                    Commands.MUTE_TOGGLE, Commands.MUTE, Commands.UNMUTE,
                    "shuffle", "repeat", "seek", "stop", "fast_forward", "rewind"
                ]
                
                if cmd_id in premium_commands:
                    _LOG.info("Command %s requires Spotify Premium - ignoring for Free user", cmd_id)
                    return ucapi.StatusCodes.OK
            
            # Handle Premium commands
            if cmd_id == Commands.PLAY_PAUSE:
                return await self._handle_play_pause()
            elif cmd_id == Commands.NEXT:
                return await self._handle_next()
            elif cmd_id == Commands.PREVIOUS:
                return await self._handle_previous()
            elif cmd_id == Commands.VOLUME:
                return await self._handle_volume(params)
            elif cmd_id == Commands.VOLUME_UP:
                return await self._handle_volume_up()
            elif cmd_id == Commands.VOLUME_DOWN:
                return await self._handle_volume_down()
            else:
                _LOG.info("Unhandled command %s - ignoring", cmd_id)
                return ucapi.StatusCodes.OK
                
        except Exception as e:
            _LOG.error("Error handling command %s: %s", cmd_id, e)
            return ucapi.StatusCodes.SERVER_ERROR
    
    async def _handle_play_pause(self) -> ucapi.StatusCodes:
        """Handle play/pause command."""
        success = await self._client.play_pause()
        return ucapi.StatusCodes.OK if success else ucapi.StatusCodes.SERVER_ERROR
    
    async def _handle_next(self) -> ucapi.StatusCodes:
        """Handle next track command."""
        success = await self._client.next_track()
        return ucapi.StatusCodes.OK if success else ucapi.StatusCodes.SERVER_ERROR
    
    async def _handle_previous(self) -> ucapi.StatusCodes:
        """Handle previous track command."""
        success = await self._client.previous_track()
        return ucapi.StatusCodes.OK if success else ucapi.StatusCodes.SERVER_ERROR
    
    async def _handle_volume(self, params: dict[str, Any] | None) -> ucapi.StatusCodes:
        """Handle volume set command."""
        if not params or "volume" not in params:
            return ucapi.StatusCodes.BAD_REQUEST
        
        volume = params["volume"]
        success = await self._client.set_volume(volume)
        
        if success:
            self._api.configured_entities.update_attributes(self.entity.id, {Attributes.VOLUME: volume})
        
        return ucapi.StatusCodes.OK if success else ucapi.StatusCodes.SERVER_ERROR
    
    async def _handle_volume_up(self) -> ucapi.StatusCodes:
        """Handle volume up command."""
        current_volume = self.entity.attributes.get(Attributes.VOLUME, 50)
        new_volume = min(100, current_volume + 5)
        return await self._handle_volume({"volume": new_volume})
    
    async def _handle_volume_down(self) -> ucapi.StatusCodes:
        """Handle volume down command."""
        current_volume = self.entity.attributes.get(Attributes.VOLUME, 50)
        new_volume = max(0, current_volume - 5)
        return await self._handle_volume({"volume": new_volume})
    
    async def _handle_on(self) -> ucapi.StatusCodes:
        """Handle turn on command."""
        if not self._config.is_premium_user():
            _LOG.info("ON command acknowledged for Free user (display only)")
            return ucapi.StatusCodes.OK

        success = await self._client.play()
        if success:
            self._api.configured_entities.update_attributes(self.entity.id, {Attributes.STATE: States.PLAYING})
        return ucapi.StatusCodes.OK if success else ucapi.StatusCodes.SERVER_ERROR
    
    async def _handle_off(self) -> ucapi.StatusCodes:
        """Handle turn off command."""
        if not self._config.is_premium_user():
            _LOG.info("OFF command acknowledged for Free user (display only)")
            return ucapi.StatusCodes.OK

        success = await self._client.pause()
        if success:
            self._api.configured_entities.update_attributes(self.entity.id, {Attributes.STATE: States.PAUSED})
        return ucapi.StatusCodes.OK if success else ucapi.StatusCodes.SERVER_ERROR
    
    async def update_current_track(self, track_data: Dict[str, Any]) -> None:
        """Update media player with current track information."""
        try:
            attributes = {}
            
            if track_data.get("is_playing", False):
                attributes[Attributes.STATE] = States.PLAYING
            else:
                attributes[Attributes.STATE] = States.PAUSED
            
            attributes[Attributes.MEDIA_TITLE] = track_data.get("title", "")
            attributes[Attributes.MEDIA_ARTIST] = ", ".join(track_data.get("artists", []))
            attributes[Attributes.MEDIA_ALBUM] = track_data.get("album", "")
            attributes[Attributes.MEDIA_DURATION] = track_data.get("duration_ms", 0) // 1000
            attributes[Attributes.MEDIA_POSITION] = track_data.get("progress_ms", 0) // 1000
            attributes[Attributes.MEDIA_IMAGE_URL] = track_data.get("image_url", "")
            attributes[Attributes.VOLUME] = track_data.get("volume_percent", 50)
            attributes[Attributes.MUTED] = track_data.get("volume_percent", 50) == 0

            # Only send update if attributes have changed
            changed_attrs = {k: v for k, v in attributes.items() if self.entity.attributes.get(k) != v}

            if changed_attrs:
                self._api.configured_entities.update_attributes(self.entity.id, changed_attrs)
                _LOG.debug(f"Updated track info: {changed_attrs}")
            
        except Exception as e:
            _LOG.error("Error updating current track: %s", e)
    
    async def clear_current_track(self) -> None:
        """Clear current track information when nothing is playing."""
        try:
            attributes = {
                Attributes.STATE: States.OFF,
                Attributes.MEDIA_TITLE: "",
                Attributes.MEDIA_ARTIST: "",
                Attributes.MEDIA_ALBUM: "",
                Attributes.MEDIA_DURATION: 0,
                Attributes.MEDIA_POSITION: 0,
                Attributes.MEDIA_IMAGE_URL: ""
            }
            
            if self.entity.attributes.get(Attributes.STATE) != States.OFF:
                self._api.configured_entities.update_attributes(self.entity.id, attributes)
                _LOG.debug("Cleared current track information")
            
        except Exception as e:
            _LOG.error("Error clearing current track: %s", e)