# Spotify Integration for Unfolded Circle Remote 2/3

Control Spotify playback and view currently playing track information on your Unfolded Circle Remote 2 or Remote 3 with **real-time updates**, **album artwork**, and **full playback control** (Premium users).

![Spotify](https://img.shields.io/badge/Spotify-1DB954?style=flat-square&logo=spotify&logoColor=white)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-spotify?style=flat-square)](https://github.com/mase1981/uc-intg-spotify/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-spotify?style=flat-square)](https://github.com/mase1981/uc-intg-spotify/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://community.unfoldedcircle.com/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-spotify/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)


## Features

This integration provides comprehensive Spotify control directly from your Unfolded Circle Remote, with different feature sets for Free and Premium users.

**IMPORTANT:** Requires creating your own Spotify Developer App (free, 5 minutes). Full setup instructions below.

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

### 🎵 **For All Users (Free & Premium)**

- **Real-time Track Display** - Title, artist, album with artwork
- **Playback Progress** - Live position and duration tracking
- **Album Artwork** - High-quality cover art display
- **State Updates** - Every 30 seconds (configurable)

### ⚡ **For Spotify Premium Users Only**

- **Play/Pause Control** - Toggle playback
- **Track Navigation** - Next/previous track
- **Volume Control** - Set volume or use up/down
- **Physical Button Mapping** - UC Remote hardware buttons
- **Remote Entity** - Custom UI with playback controls

### Feature Comparison

| Feature | Free Users | Premium Users |
|---------|------------|---------------|
| Track Display | ✅ Full | ✅ Full |
| Album Artwork | ✅ Yes | ✅ Yes |
| Playback Progress | ✅ Yes | ✅ Yes |
| Play/Pause Control | ❌ No | ✅ Yes |
| Next/Previous | ❌ No | ✅ Yes |
| Volume Control | ❌ No | ✅ Yes |
| Button Mapping | ❌ No | ✅ Yes |

### **Protocol Requirements**

- **Protocol**: Spotify Web API
- **Authentication**: OAuth 2.0 Authorization Code Flow
- **Token Management**: Automatic refresh
- **Internet Required**: Cloud-based integration
- **Polling**: 30-second intervals (configurable)

### **Network Requirements**

- **Internet Connection** - Required for Spotify API access
- **HTTPS Access** - Outbound HTTPS traffic
- **Bandwidth** - Minimal (artwork + metadata)
- **Developer App** - Spotify Developer App (free to create)

## Prerequisites

### Spotify Developer App Setup

**BEFORE INSTALLATION:** You must create a Spotify Developer App to get your Client ID and Client Secret.

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create App"**
4. Fill in the details:
   - **App Name**: `UC Remote Integration` (or any name)
   - **App Description**: `Unfolded Circle Remote integration`
   - **Redirect URI**: `https://example.com/callback` ⚠️ **Must be exactly this**
   - **API**: Check **"Web API"**
5. Click **"Save"**
6. Note your **Client ID** and **Client Secret** (click "Show Client Secret")

#### Important Notes:
- ✅ Keep credentials secure - don't share them
- ✅ Redirect URI must be **exactly** `https://example.com/callback`
- ✅ Both Free and Premium accounts can create apps
- ✅ No recurring costs - one-time setup

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-spotify/releases) page
2. Download the latest `uc-intg-spotify-<version>-aarch64.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

The integration is available as a pre-built Docker image from GitHub Container Registry:

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
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-spotify --restart unless-stopped --network host -v spotify-config:/app/config -e UC_CONFIG_HOME=/app/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-spotify:latest
```

## Configuration

### Step 1: Enter App Credentials

1. After installation, go to **Settings** → **Integrations** → Spotify
2. Click **"Configure"**
3. Enter your **Spotify Client ID**
4. Enter your **Spotify Client Secret**
5. Select if you have **Spotify Premium**
6. Click **Next**

### Step 2: Authentication

1. **Click the Spotify authorization URL** (opens in browser)
2. Log into your Spotify account
3. Click **Agree** to authorize
4. Browser shows "page not found" - **this is normal!**
5. **Copy the authorization code** from browser address bar:
   - Look for `code=...` in the URL
   - Copy everything after `code=` (long string ~100+ characters)
   - Or paste the entire callback URL
6. **Paste code** into setup form
7. Click **Finish**

### Step 3: Completion

Two entities are created:
- **Spotify Player** (Media Player entity)
- **Spotify Remote** (Remote entity with controls)

## Using the Integration

### Media Player Entity

**Display Features (All Users)**:
- Currently playing track information
- Album artwork
- Real-time playback progress
- Track duration and position

**Control Features (Premium Only)**:
- Play/pause button
- Next/previous track buttons
- Volume control slider
- Volume up/down buttons

### Remote Entity

**For Premium Users**:
- Physical button mappings:
  - **Play** → Play/Pause
  - **Next** → Next Track
  - **Prev** → Previous Track
  - **Volume Up** → Increase Volume
  - **Volume Down** → Decrease Volume
- Custom UI with playback controls
- Synchronized state with Spotify

**For Free Users**:
- Display-only entity
- Shows message: "Spotify Premium required for playback control"

## Credits

- **Developer**: Meir Miyara
- **Spotify**: Music streaming platform
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Protocol**: Spotify Web API with OAuth 2.0
- **Community**: Testing and feedback from UC community

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see LICENSE file for details.

## Legal Disclaimers

### Third-Party Service Integration

This integration is an **independent, unofficial project** that interfaces with Spotify's publicly available Web API:

- ❌ **NOT** sponsored, endorsed, or affiliated with Spotify AB
- ❌ **NOT** an official Spotify product or service
- ✅ Developed independently using Spotify's public API
- ✅ Open source under MPL-2.0 license

### Terms of Service

By using this integration, you agree to:

- ✅ Comply with [Spotify Developer Terms](https://developer.spotify.com/terms)
- ✅ Comply with [Spotify Web API Terms](https://developer.spotify.com/terms)
- ✅ Create and manage your own Spotify Developer App
- ✅ Accept responsibility for your API usage
- ✅ Use at your own risk

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-spotify/issues)
- **UC Community Forum**: [General discussion and support](https://community.unfoldedcircle.com/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **Spotify Support**: [Official Spotify Support](https://support.spotify.com/)

---

**Made with ❤️ for the Unfolded Circle and Spotify Communities**

**Thank You**: Meir Miyara
