# Spotify Integration for Unfolded Circle Remote 2/3

Control Spotify playback from your Unfolded Circle Remote with full media browsing, device switching, and real-time updates.

![Spotify](https://img.shields.io/badge/Spotify-1DB954?style=flat-square&logo=spotify&logoColor=white)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-spotify?style=flat-square)](https://github.com/mase1981/uc-intg-spotify/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-spotify?style=flat-square)](https://github.com/mase1981/uc-intg-spotify/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-spotify/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)

## Requirements

- **Spotify Premium** account (API no longer supports Free accounts)
- Spotify Developer App (free, 5-minute setup)

## Features

### Entities

| Entity | Description |
|--------|-------------|
| **Media Player** | Full playback control with artwork, progress, browse, and search |
| **Remote** | Physical button mappings and custom UI |
| **Device Select** | Switch between Spotify Connect devices |
| **Now Playing Sensor** | Current track info as text |
| **Active Device Sensor** | Currently active playback device |

### Playback Control

- Play/pause, next, previous, seek
- Volume control (precise 1% steps)
- Shuffle and repeat toggle
- Album artwork and live progress

### Media Browsing & Search

- Browse your playlists, saved albums, liked songs
- Browse top tracks, top artists, followed artists
- Browse recently played, new releases
- Full-text search across tracks, albums, artists, and playlists
- Play any item directly from browse/search results

### Spotify Connect Device Switching

- Switch playback between all your Spotify Connect devices
- **Zeroconf/mDNS discovery** finds devices on your local network (even when idle)
- **Device caching** keeps recently-seen devices available for 24 hours
- **Smart name resolution** queries devices directly for their real friendly names
- Devices from three sources: Spotify API + Zeroconf + Cache

## Prerequisites

### Spotify Developer App Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your **Premium** Spotify account
3. Click **"Create App"**
4. Fill in:
   - **App Name**: `UC Remote` (or any name)
   - **Redirect URI**: `https://example.com/callback` (must be exact)
   - **API**: Check **"Web API"**
5. Click **"Save"**
6. Note your **Client ID** and **Client Secret**

## Installation

### Option 1: Remote Web Interface (Recommended)

1. Download the latest `.tar.gz` from [Releases](https://github.com/mase1981/uc-intg-spotify/releases)
2. Open your remote's web interface (`http://your-remote-ip`)
3. Go to **Settings** → **Integrations** → **Add Integration** → **Upload**

### Option 2: Docker

```yaml
services:
  uc-intg-spotify:
    image: ghcr.io/mase1981/uc-intg-spotify:latest
    container_name: uc-intg-spotify
    network_mode: host
    volumes:
      - </local/path>:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_INTERFACE=0.0.0.0
    restart: unless-stopped
```

## Configuration

1. After installation, go to **Settings** → **Integrations** → **Spotify** → **Configure**
2. Enter your **Client ID** and **Client Secret**
3. Click the authorization URL, log in, and approve
4. Copy the `code=...` value from the redirect URL (or paste the entire URL)
5. Done — all entities are created automatically

## Support Development

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

## License

Mozilla Public License 2.0 (MPL-2.0)

## Disclaimer

This is an independent, unofficial project using Spotify's public Web API. Not affiliated with or endorsed by Spotify AB.
