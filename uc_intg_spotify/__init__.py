"""Spotify integration for Unfolded Circle Remote. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
import asyncio
import json
import logging
import os
from pathlib import Path

from ucapi import DeviceStates
from ucapi_framework import BaseConfigManager, get_config_path

from uc_intg_spotify.config import SpotifyDeviceConfig
from uc_intg_spotify.driver import SpotifyDriver
from uc_intg_spotify.setup import SpotifySetupFlow

try:
    driver_path = Path(__file__).parent.parent / "driver.json"
    with open(driver_path, "r", encoding="utf-8") as f:
        __version__ = json.load(f).get("version", "0.0.0")
except (FileNotFoundError, json.JSONDecodeError):
    __version__ = "0.0.0"

_LOG = logging.getLogger(__name__)


async def main() -> None:
    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.DEBUG),
        format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
    )
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("websockets.server").setLevel(logging.CRITICAL)
    _LOG.info("Starting Spotify integration v%s", __version__)

    driver = SpotifyDriver()
    config_path = get_config_path(driver.api.config_dir_path or "")
    config_manager = BaseConfigManager(
        config_path,
        add_handler=driver.on_device_added,
        remove_handler=driver.on_device_removed,
        config_class=SpotifyDeviceConfig,
    )
    driver.config_manager = config_manager

    setup_handler = SpotifySetupFlow.create_handler(driver)
    driver_json_path = os.path.join(os.path.dirname(__file__), "..", "driver.json")
    await driver.api.init(os.path.abspath(driver_json_path), setup_handler)
    await driver.register_all_device_instances(connect=False)

    device_count = len(list(config_manager.all()))
    await driver.api.set_device_state(
        DeviceStates.CONNECTED if device_count > 0 else DeviceStates.DISCONNECTED
    )
    _LOG.info("Spotify integration started - %d device(s) configured", device_count)
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
