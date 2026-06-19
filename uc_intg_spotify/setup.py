"""Spotify setup flow. :copyright: (c) 2024 by Meir Miyara. :license: MPL-2.0"""
from __future__ import annotations

import logging
from typing import Any

from ucapi import RequestUserInput
from ucapi_framework import BaseSetupFlow

from uc_intg_spotify.client import SpotifyClient
from uc_intg_spotify.config import SpotifyDeviceConfig

_LOG = logging.getLogger(__name__)


class SpotifySetupFlow(BaseSetupFlow[SpotifyDeviceConfig]):
    """Setup flow for Spotify integration using OAuth2."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._client_id: str = ""
        self._client_secret: str = ""

    def get_manual_entry_form(self) -> RequestUserInput:
        existing_client_id = ""
        existing_client_secret = ""
        if self._selected_config_id:
            existing = self.config.get(self._selected_config_id)
            if existing:
                existing_client_id = existing.client_id
                existing_client_secret = existing.client_secret

        return RequestUserInput(
            {"en": "Spotify Setup"},
            [
                {
                    "id": "info",
                    "label": {"en": "Setup Instructions"},
                    "field": {
                        "label": {
                            "value": {
                                "en": "IMPORTANT: Spotify Premium is required.\n\n"
                                "1. Go to https://developer.spotify.com/dashboard\n"
                                "2. Log in and click 'Create App'\n"
                                "3. App Name: 'UC Remote Integration'\n"
                                "4. Redirect URI: https://example.com/callback\n"
                                "5. Check 'Web API' and save\n"
                                "6. Copy Client ID and Client Secret below\n\n"
                                "Re-authenticating? Confirm the values below and continue "
                                "to sign in again (Spotify refresh tokens expire after 6 months)."
                            }
                        }
                    },
                },
                {
                    "id": "client_id",
                    "label": {"en": "Spotify Client ID"},
                    "field": {"text": {"value": existing_client_id}},
                },
                {
                    "id": "client_secret",
                    "label": {"en": "Spotify Client Secret"},
                    "field": {"text": {"value": existing_client_secret}},
                },
            ],
        )

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> SpotifyDeviceConfig | RequestUserInput:
        if "auth_code" in input_values:
            return await self._handle_auth_code(input_values)

        client_id = input_values.get("client_id", "").strip()
        client_secret = input_values.get("client_secret", "").strip()

        if not client_id or not client_secret:
            raise ValueError("Both Client ID and Client Secret are required")

        self._client_id = client_id
        self._client_secret = client_secret

        client = SpotifyClient()
        auth_url = client.get_authorization_url(client_id)

        return RequestUserInput(
            {"en": "Spotify Authentication"},
            [
                {
                    "id": "instructions",
                    "label": {"en": "Authentication Instructions"},
                    "field": {
                        "label": {
                            "value": {
                                "en": "1. Click the URL below to open in a browser\n"
                                "2. Log in and authorize the application\n"
                                "3. You'll see 'page not found' - this is normal!\n"
                                "4. Copy the 'code=...' value from your browser's address bar\n"
                                "5. Paste the code or full URL below"
                            }
                        }
                    },
                },
                {
                    "id": "spotify_url",
                    "label": {"en": "Spotify Authorization URL"},
                    "field": {"text": {"value": auth_url, "read_only": True}},
                },
                {
                    "id": "auth_code",
                    "label": {"en": "Paste Code or Full URL"},
                    "field": {"text": {"value": "", "placeholder": "Paste here..."}},
                },
            ],
        )

    async def _handle_auth_code(
        self, input_values: dict[str, Any]
    ) -> SpotifyDeviceConfig:
        auth_input = input_values.get("auth_code", "").strip()
        if not auth_input:
            raise ValueError("Authorization code is required")

        auth_code = auth_input
        if "code=" in auth_input:
            try:
                code_part = auth_input.split("code=")[1]
                auth_code = code_part.split("&")[0]
            except (IndexError, ValueError):
                raise ValueError("Could not extract code from URL")

        client = SpotifyClient()
        token_data = await client.exchange_code_for_token(
            auth_code, self._client_id, self._client_secret
        )

        if not token_data:
            await client.close()
            raise ConnectionError("Failed to authenticate with Spotify")

        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data.get("expires_in", 3600)

        client.set_tokens(access_token, refresh_token)
        profile = await client.get_user_profile()
        await client.close()

        user_id = (profile or {}).get("id", "")
        display_name = ((profile or {}).get("display_name") or "").strip()

        identifier, name = self._resolve_account_identity(user_id, display_name)

        import time

        return SpotifyDeviceConfig(
            identifier=identifier,
            name=name,
            client_id=self._client_id,
            client_secret=self._client_secret,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=int(time.time()) + expires_in - 60,
            user_id=user_id,
        )

    def _resolve_account_identity(
        self, user_id: str, display_name: str
    ) -> tuple[str, str]:
        """Map a Spotify account to a stable identifier and display name.

        The first/primary account keeps the legacy ``spotify`` identifier so existing
        installs (and their activities) are preserved. Additional accounts are keyed by
        the Spotify profile id, mirroring Home Assistant's per-account config entries.
        """
        if self._selected_config_id:
            existing = self.config.get(self._selected_config_id)
            name = display_name or (existing.name if existing else "") or "Spotify"
            return self._selected_config_id, name

        existing_accounts = list(self.config.all())

        if user_id:
            for account in existing_accounts:
                if getattr(account, "user_id", "") == user_id:
                    raise ValueError(
                        f"This Spotify account ({display_name or user_id}) is already configured"
                    )

        if not existing_accounts:
            return "spotify", display_name or "Spotify"

        if not user_id:
            raise ConnectionError(
                "Could not read the Spotify profile needed to add another account. Please try again."
            )

        return f"spotify_{user_id}", display_name or f"Spotify ({user_id})"
