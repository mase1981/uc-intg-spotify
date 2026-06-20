# Spotify Integration for Unfolded Circle Remote 2/3

Control Spotify playback directly from your Unfolded Circle Remote 2 or Remote 3 with **full media browsing**, **search**, **Spotify Connect device switching and waking**, **multiple accounts**, and **real-time playback updates** with album artwork.

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

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

## Features

### 🎵 Media Player

- **Playback Controls** — Play/Pause, Next, Previous, Seek, Shuffle, Repeat
- **Volume Management** — Precise 1% step volume control with instant UI feedback
- **Media Information** — Title, artist, album with high-quality artwork and live progress
- **Source Selection** — Switch between all Spotify Connect devices
- **Real-time Updates** — 10-second polling with optimistic state updates

### 📂 Media Browser

Browse and play your Spotify library directly from the Remote's media browser:

- **Playlists** — All your playlists with artwork
- **Saved Albums** — Your album library
- **Liked Songs** — Saved tracks collection
- **Top Tracks** — Your most-played tracks
- **Top Artists** — Your most-listened artists with top tracks and discography
- **Followed Artists** — Artists you follow
- **Recently Played** — Recent listening history
- **New Releases** — Latest album releases
- **Search** — Full-text search across tracks, albums, artists, and playlists
- **Availability Aware** — Tracks not available in your country are marked non-playable instead of failing silently

### 🔊 Spotify Connect Device Switching & Waking

- **Wake Inactive Devices** — Select a device that is powered and on the network but not signed into Spotify, and the integration wakes it (Zeroconf `addUser`) and transfers playback — no password needed
- **Three-Source Discovery** — Devices from Spotify API + Zeroconf/mDNS + 24h cache
- **Zeroconf/mDNS** — Discovers devices on your local network (even when idle)
- **Smart Name Resolution** — Queries each device's getInfo endpoint for real friendly names
- **Device Caching** — Previously-seen devices remain available for 24 hours
- **Instant Switching** — Transfer playback between devices with one tap

> **Waking notes:** Works with modern Spotify Connect devices (WiiM, Marantz/Denon HEOS, most certified AVRs & soundbars). A fully powered‑off device must be powered on first (e.g. via your AVR integration). Pure librespot devices (Raspotify/spotifyd) are discovered but cannot be woken this way. Requires the `streaming` permission — see [Upgrading](#upgrading).

### 👥 Multiple Accounts

- **Add More Than One Account** — Reconfigure the integration and choose **"Add a new device"** to sign in with another Spotify account
- **Independent Entities** — Each account gets its own player, remote, select, and sensors, labeled by account name
- **Backward Compatible** — Your first/primary account keeps its original entity IDs; additional accounts are keyed by Spotify profile

### 🎮 Remote Control

- **Physical Button Mapping** — Play/Pause, Next, Previous, Volume Up/Down
- **Custom UI Page** — Playback controls with shuffle and repeat
- **Simple Commands** — Play, Pause, Next, Previous, Volume Up/Down, Shuffle, Repeat

### 📊 Sensors

- **Now Playing** — Current track title and artist as text
- **Active Device** — Currently active Spotify Connect playback device

### 🎛️ Select Entity

- **Active Device** — Browse and switch between all discovered Spotify Connect devices with next/previous cycling

### Protocol & Requirements

- **Protocol**: Spotify Web API (OAuth 2.0 Authorization Code Flow) + Spotify Connect Zeroconf for device waking
- **Account**: Spotify Premium required (API no longer supports Free accounts); multiple accounts supported
- **Permissions**: Includes the `streaming` scope, required to wake Spotify Connect devices
- **Internet**: Required for Spotify API access
- **Local Network**: Required for Zeroconf device discovery
- **Polling**: 10-second intervals (configurable)
- **Token Management**: Automatic refresh with persistence

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-spotify/releases) page
2. Download the latest `uc-intg-spotify-<version>-aarch64.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

**Image**: `ghcr.io/mase1981/uc-intg-spotify:latest`

**Docker Compose:**
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
      - UC_INTEGRATION_HTTP_PORT=9090
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name=uc-intg-spotify --network host -v </local/path>:/data -e UC_CONFIG_HOME=/data -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app --restart unless-stopped ghcr.io/mase1981/uc-intg-spotify:latest
```

## Prerequisites

### Spotify Developer App Setup

**BEFORE INSTALLATION:** Create a Spotify Developer App (free, 5 minutes):

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your **Premium** Spotify account
3. Click **"Create App"**
4. Fill in:
   - **App Name**: `UC Remote` (or any name)
   - **App Description**: `Unfolded Circle Remote integration`
   - **Redirect URI**: `https://example.com/callback` ⚠️ **Must be exactly this**
   - **API**: Check **"Web API"**
5. Click **"Save"**
6. Note your **Client ID** and **Client Secret** (click "Show Client Secret")

#### Important Notes:
- ✅ **Spotify Premium required** — API no longer supports Free accounts
- ✅ Redirect URI must be **exactly** `https://example.com/callback`
- ✅ Keep credentials secure — don't share them
- ✅ No recurring costs — one-time setup

## Configuration

### Step 1: Enter App Credentials

1. After installation, go to **Settings** → **Integrations** → **Spotify**
2. Click **"Configure"**
3. Enter your **Spotify Client ID**
4. Enter your **Spotify Client Secret**
5. Click **Next**

### Step 2: Authentication

1. Click the Spotify authorization URL displayed on screen
2. Log into your Spotify account and click **Agree**
3. Browser shows "page not found" — **this is normal!**
4. Copy the `code=...` value from the browser address bar (or paste the entire URL)
5. Paste into setup form and click **Finish**

### Step 3: Completion

Five entities are created automatically:
- **Spotify Player** — Media Player with browse, search, and playback control
- **Spotify Remote** — Remote entity with button mappings and custom UI
- **Spotify Active Device** — Select entity for device switching
- **Spotify Now Playing** — Sensor showing current track
- **Spotify Active Device** — Sensor showing active playback device

### Adding Another Account

1. Go to **Settings** → **Integrations** → **Spotify** → **Configure**
2. Choose **"Add a new device"**
3. Enter Client ID/Secret (you can reuse the same Spotify app) and authorize — **sign in with the other Spotify account** on the consent screen
4. A second set of entities is created, labeled with that account's name

## Upgrading

Device waking adds the Spotify **`streaming`** permission. After upgrading from a version before 3.4.0, **reconfigure the integration and sign in again** so the new permission is granted. Existing playback control keeps working without it, but waking inactive devices will not.

## Credits

- **Developer**: Meir Miyara
- **Protocol**: Spotify Web API with OAuth 2.0
- **Framework**: Unfolded Circle ucapi-framework
- **Discovery**: Zeroconf/mDNS for Spotify Connect device resolution
- **Inspiration**: Spotify Connect device waking (Zeroconf) and multi-account approach inspired by Todd Lucas ([thlucas1](https://github.com/thlucas1)) — [SpotifyPlus for Home Assistant](https://github.com/thlucas1/homeassistantcomponent_spotifyplus) and the [SpotifyWebApiPython](https://github.com/thlucas1/SpotifyWebApiPython) library
- **Community**: Testing and feedback from UC community

## License

This project is licensed under the MPL-2.0 License - see LICENSE file for details.

## Legal Disclaimer

This is an **independent, unofficial project** using Spotify's public Web API. Not sponsored, endorsed, or affiliated with Spotify AB.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-spotify/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **Spotify Support**: [Official Spotify Support](https://support.spotify.com/)

---

**Made with ❤️ for the Unfolded Circle and Spotify Communities — Thank You: Meir Miyara**
