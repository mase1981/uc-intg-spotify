"""
Spotify remote entity for Unfolded Circle integration.

:copyright: (c) 2024
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any, Dict

import ucapi
from ucapi.remote import Commands, Features, States
from ucapi.ui import Buttons, Size, create_btn_mapping, create_ui_icon, create_ui_text, UiPage

from uc_intg_spotify.client import SpotifyClient
from uc_intg_spotify.config import SpotifyConfig

_LOG = logging.getLogger(__name__)


class SpotifyRemote:
    """Spotify remote entity."""
    
    def __init__(self, api: ucapi.IntegrationAPI, client: SpotifyClient):
        """Initialize Spotify remote."""
        self._api = api
        self._client = client
        self._config: SpotifyConfig = client._config if client else None
        
        features = [Features.ON_OFF]
        if self._config and self._config.is_premium_user():
            features.append(Features.SEND_CMD)
        
        simple_commands = []
        button_mapping = []
        
        # Add premium features for premium users
        if self._config and self._config.is_premium_user():
            simple_commands = [
                "PLAY_PAUSE",
                "NEXT",
                "PREVIOUS",
                "VOLUME_UP", 
                "VOLUME_DOWN"
            ]
            
            button_mapping = [
                create_btn_mapping(Buttons.PLAY, "PLAY_PAUSE"),
                create_btn_mapping(Buttons.NEXT, "NEXT"), 
                create_btn_mapping(Buttons.PREV, "PREVIOUS"),
                create_btn_mapping(Buttons.VOLUME_UP, "VOLUME_UP"),
                create_btn_mapping(Buttons.VOLUME_DOWN, "VOLUME_DOWN"),
            ]
        
        ui_pages = self._create_ui_pages()
        
        self.entity = ucapi.Remote(
            identifier="spotify_remote_main",
            name={"en": "Spotify Remote"},
            features=features,
            attributes={"state": States.ON},
            simple_commands=simple_commands,
            button_mapping=button_mapping,
            ui_pages=ui_pages,
            cmd_handler=self.cmd_handler
        )
        
        _LOG.info("Spotify remote entity created")
    
    def _create_ui_pages(self) -> list[UiPage]:
        """Create UI pages for the remote."""
        pages = []
        
        main_page = UiPage(page_id="main", name="Spotify Controls", grid=Size(4, 6))
        
        if self._config and self._config.is_premium_user():
            main_page.add(create_ui_icon("uc:play-pause", 1, 1, Size(2, 1), "PLAY_PAUSE"))
            main_page.add(create_ui_icon("uc:backward", 0, 2, Size(1, 1), "PREVIOUS"))
            main_page.add(create_ui_icon("uc:forward", 3, 2, Size(1, 1), "NEXT"))
            main_page.add(create_ui_icon("uc:volume-high", 1, 3, Size(1, 1), "VOLUME_UP"))
            main_page.add(create_ui_icon("uc:volume-low", 2, 3, Size(1, 1), "VOLUME_DOWN"))
        else:
            main_page.add(create_ui_text("Spotify Premium required", 0, 1, Size(4, 1)))
            main_page.add(create_ui_text("for playback control", 0, 2, Size(4, 1)))
            main_page.add(create_ui_text("Display only mode", 0, 4, Size(4, 1)))
        
        pages.append(main_page)
        return pages
    
    async def cmd_handler(self, entity: ucapi.Entity, cmd_id: str, params: dict[str, Any] | None) -> ucapi.StatusCodes:
        """Handle remote commands."""
        _LOG.info("Remote command: %s %s", cmd_id, params)
        
        if not self._client or not self._client.is_authenticated():
            _LOG.warning("Spotify client not authenticated")
            return ucapi.StatusCodes.SERVICE_UNAVAILABLE
        
        try:
            if cmd_id == Commands.ON:
                return await self._handle_on()
            elif cmd_id == Commands.OFF:
                return await self._handle_off()
            elif cmd_id == Commands.SEND_CMD:
                return await self._handle_send_cmd(params)
            else:
                _LOG.info("Unsupported remote command: %s", cmd_id)
                return ucapi.StatusCodes.NOT_IMPLEMENTED
                
        except Exception as e:
            _LOG.error("Error handling remote command %s: %s", cmd_id, e)
            return ucapi.StatusCodes.SERVER_ERROR
    
    async def _handle_on(self) -> ucapi.StatusCodes:
        """Handle remote on command."""
        self._api.configured_entities.update_attributes(self.entity.id, {"state": States.ON})
        return ucapi.StatusCodes.OK
    
    async def _handle_off(self) -> ucapi.StatusCodes:
        """Handle remote off command.""" 
        self._api.configured_entities.update_attributes(self.entity.id, {"state": States.OFF})
        return ucapi.StatusCodes.OK
    
    async def _handle_send_cmd(self, params: dict[str, Any] | None) -> ucapi.StatusCodes:
        """Handle send command."""
        if not self._config.is_premium_user():
            _LOG.info("Send command requires Spotify Premium")
            return ucapi.StatusCodes.NOT_IMPLEMENTED
        
        if not params or "command" not in params:
            return ucapi.StatusCodes.BAD_REQUEST
        
        command = params["command"]
        _LOG.debug("Executing remote command for Premium user: %s", command)
        
        success = False
        if command == "PLAY_PAUSE":
            success = await self._client.play_pause()
        elif command == "NEXT":
            success = await self._client.next_track()
        elif command == "PREVIOUS":
            success = await self._client.previous_track()
        elif command == "VOLUME_UP":
            current_state = await self._client.get_playback_state()
            if current_state:
                if not current_state.get("supports_volume", False):
                    _LOG.info("Active device does not support volume control")
                    return ucapi.StatusCodes.NOT_IMPLEMENTED
                current_volume = current_state.get("volume_percent", 50)
                new_volume = min(100, current_volume + 10)
                success = await self._client.set_volume(new_volume)
            else:
                success = False
        elif command == "VOLUME_DOWN":
            current_state = await self._client.get_playback_state()
            if current_state:
                if not current_state.get("supports_volume", False):
                    _LOG.info("Active device does not support volume control")
                    return ucapi.StatusCodes.NOT_IMPLEMENTED
                current_volume = current_state.get("volume_percent", 50)
                new_volume = max(0, current_volume - 10)
                success = await self._client.set_volume(new_volume)
            else:
                success = False
        else:
            _LOG.warning("Unknown remote command: %s", command)
            return ucapi.StatusCodes.NOT_IMPLEMENTED
        
        return ucapi.StatusCodes.OK if success else ucapi.StatusCodes.SERVER_ERROR