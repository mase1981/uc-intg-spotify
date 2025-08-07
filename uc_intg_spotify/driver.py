#!/usr/bin/env python3
"""
Spotify integration driver for Unfolded Circle Remote Two.

:copyright: (c) 2024
:license: MPL-2.0, see LICENSE for more details.
"""
import asyncio
import logging
import os
import signal
from typing import Optional

import ucapi

from uc_intg_spotify.client import SpotifyClient
from uc_intg_spotify.config import SpotifyConfig
from uc_intg_spotify.media_player import SpotifyMediaPlayer
from uc_intg_spotify.remote import SpotifyRemote
from uc_intg_spotify.setup import SpotifySetup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)8s | %(name)s | %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

_LOG = logging.getLogger(__name__)

# Global State
loop = asyncio.get_event_loop()
api: Optional[ucapi.IntegrationAPI] = None
spotify_client: Optional[SpotifyClient] = None
spotify_config: Optional[SpotifyConfig] = None
media_player: Optional[SpotifyMediaPlayer] = None

async def on_setup_complete():
    """Callback executed when driver setup is complete."""
    global media_player, spotify_client, api
    _LOG.info("Setup complete. Creating entities...")

    if not api or not spotify_client:
        _LOG.error("Cannot create entities: API or client not initialized.")
        await api.set_device_state(ucapi.DeviceStates.ERROR)
        return

    # Create Media Player and Remote Entities
    media_player = SpotifyMediaPlayer(api, spotify_client)
    api.available_entities.add(media_player.entity)
    
    remote = SpotifyRemote(api, spotify_client)
    api.available_entities.add(remote.entity)
    
    _LOG.info("Entities created. Setting state to CONNECTED.")
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)

async def on_r2_connect():
    """Handle Remote Two connection."""
    _LOG.info("Remote Two connected.")
    if api and spotify_config and spotify_config.is_configured():
        _LOG.info("Re-confirming CONNECTED state for already configured integration.")
        await api.set_device_state(ucapi.DeviceStates.CONNECTED)

async def on_subscribe_entities(entity_ids: list[str]):
    """Handle entity subscription from Remote Two."""
    _LOG.info(f"Remote subscribed to entities: {entity_ids}")
    if media_player and media_player.entity.id in entity_ids:
        await media_player.start_polling()

async def on_unsubscribe_entities(entity_ids: list[str]):
    """Handle entity unsubscription from Remote Two."""
    _LOG.info(f"Remote unsubscribed from entities: {entity_ids}")
    if media_player and media_player.entity.id in entity_ids:
        await media_player.stop_polling()

async def init_integration():
    """Initialize the integration objects and API."""
    global api, spotify_client, spotify_config
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    driver_json_path = os.path.join(project_root, "driver.json")
    
    api = ucapi.IntegrationAPI(loop)

    config_path = os.path.join(api.config_dir_path, "config.json")
    spotify_config = SpotifyConfig(config_path)
    spotify_client = SpotifyClient(spotify_config)

    setup_handler = SpotifySetup(spotify_config, spotify_client, on_setup_complete)
    
    await api.init(driver_json_path, setup_handler.setup_handler)
    
    api.add_listener(ucapi.Events.CONNECT, on_r2_connect)
    api.add_listener(ucapi.Events.SUBSCRIBE_ENTITIES, on_subscribe_entities)
    api.add_listener(ucapi.Events.UNSUBSCRIBE_ENTITIES, on_unsubscribe_entities)
    
async def main():
    """Main entry point."""
    _LOG.info("Starting Spotify Integration Driver")
    
    await init_integration()
    
    if spotify_config and not spotify_config.is_configured():
        _LOG.warning("Integration is not configured. Setting state to ERROR to prompt user setup.")
        await api.set_device_state(ucapi.DeviceStates.ERROR)
    elif spotify_config and spotify_client:
        _LOG.info("Configuration found. Refreshing tokens and connecting...")
        if await spotify_client.refresh_access_token():
            _LOG.info("Token refresh successful.")
            await on_setup_complete()
        else:
            _LOG.error("Failed to refresh tokens on startup. Setting state to ERROR.")
            await api.set_device_state(ucapi.DeviceStates.ERROR)

    _LOG.info("Integration is running. Press Ctrl+C to stop.")
    
def shutdown_handler(signum, frame):
    """Handle termination signals for graceful shutdown."""
    _LOG.warning(f"Received signal {signum}. Shutting down...")
    
    async def cleanup():
        if media_player:
            await media_player.stop_polling()
        if spotify_client:
            await spotify_client.close()
        
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        loop.stop()

    loop.create_task(cleanup())

if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except (KeyboardInterrupt, asyncio.CancelledError):
        _LOG.info("Driver stopped.")
    finally:
        if loop and not loop.is_closed():
            loop.close()