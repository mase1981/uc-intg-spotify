# Spotify Integration for Unfolded Circle Remote Two/3
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

Control Spotify playback and view currently playing track information on your Unfolded Circle Remote Two/3 with real-time updates and album artwork.

**IMPORTANT:** This integration requires creating your own Spotify Developer App (free, 5 minutes). Full setup instructions below.

---

## 🌟 Features

### For All Users (Free & Premium)
- 🎵 **Real-time Track Display** - Title, artist, album with artwork
- ⏱️ **Playback Progress** - Live position and duration tracking
- 🖼️ **Album Artwork** - High-quality cover art display
- 📊 **State Updates** - Every 30 seconds (configurable)

### For Spotify Premium Users Only
- ▶️ **Play/Pause Control** - Toggle playback
- ⏭️ **Track Navigation** - Next/previous track
- 🔊 **Volume Control** - Set volume or use up/down
- 🎮 **Physical Button Mapping** - UC Remote hardware buttons
- 🎯 **Remote Entity** - Custom UI with playback controls

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

---
## 💰 Support Development

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

## 📋 Requirements

### Hardware
- Unfolded Circle Remote Two or Remote 3
- Spotify account (Premium recommended for full control)
- Active Spotify playback session

### Software
- UC Remote firmware 1.7.0+
- Spotify Developer App (instructions below)
- Network connectivity

---

## 🔑 Spotify Developer App Setup

**BEFORE INSTALLATION:** You must create a Spotify Developer App to get your Client ID and Client Secret.

### Step 1: Create Developer App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create App"**
4. Fill in the details:
   - **App Name:** `UC Remote Integration` (or any name)
   - **App Description:** `Unfolded Circle Remote integration`
   - **Redirect URI:** `https://example.com/callback` ⚠️ **Must be exactly this**
   - **API:** Check **"Web API"**
5. Click **"Save"**
6. Note your **Client ID** and **Client Secret** (click "Show Client Secret")

### Step 2: Important Notes

- ✅ Keep credentials secure - don't share them
- ✅ Redirect URI must be **exactly** `https://example.com/callback`
- ✅ Both Free and Premium accounts can create apps
- ✅ No recurring costs - one-time setup

---

## 🚀 Installation

### Option 1: GitHub Release (Recommended)

1. Download latest `.tar.gz` from [Releases](https://github.com/mase1981/uc-intg-spotify/releases)
2. Open UC Remote configurator: `http://your-remote-ip/configurator`
3. **Integrations** → **Add Integration** → **Upload driver**
4. Select downloaded file
5. Follow setup wizard

### Option 2: Docker (One-Line)
```bash
docker run -d --name uc-spotify --restart unless-stopped --network host -v spotify-config:/app/config -e UC_CONFIG_HOME=/app/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-spotify:latest
```

### Option 3: Docker Compose
```bash
git clone https://github.com/mase1981/uc-intg-spotify.git
cd uc-intg-spotify
docker-compose up -d
```

### Option 4: Development
```bash
git clone https://github.com/mase1981/uc-intg-spotify.git
cd uc-intg-spotify
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m uc_intg_spotify.driver
```

---

## ⚙️ Setup Process

### During Integration Setup

#### Page 1: App Credentials
1. Enter your **Spotify Client ID**
2. Enter your **Spotify Client Secret**
3. Select if you have **Spotify Premium**
4. Click **Next**

#### Page 2: Authentication
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

#### Page 3: Completion
- Two entities are created:
  - **Spotify Player** (Media Player entity)
  - **Spotify Remote** (Remote entity with controls)
- ✅ Setup complete!

### Important Setup Notes

⏱️ **Token may take time to process** - Spotify API can be slow during authorization. If redirect takes 10-30 seconds, this is normal - just wait for the "page not found" screen.

🔄 **If setup fails:**
- Verify Client ID/Secret are correct
- Check Redirect URI is exactly `https://example.com/callback`
- Ensure you copied the full authorization code
- Try setup again

---

## 🎮 Usage

### Media Player Entity

**Display Features (All Users):**
- Currently playing track information
- Album artwork
- Real-time playback progress
- Track duration and position

**Control Features (Premium Only):**
- Play/pause button
- Next/previous track buttons
- Volume control slider
- Volume up/down buttons

### Remote Entity

**For Premium Users:**
- Physical button mappings:
  - **Play** → Play/Pause
  - **Next** → Next Track
  - **Prev** → Previous Track
  - **Volume Up** → Increase Volume
  - **Volume Down** → Decrease Volume
- Custom UI with playback controls
- Synchronized state with Spotify

**For Free Users:**
- Display-only entity
- Shows message: "Spotify Premium required for playback control"

---

## 🎯 Activity Integration

Use Spotify in UC Remote activities:

### Available Commands (Premium Only)
```yaml
# Playback Control
- PLAY_PAUSE
- NEXT
- PREVIOUS

# Volume Control  
- VOLUME_UP
- VOLUME_DOWN
- Set volume to 50%
```

### Example Activity Sequences

**Start Music Session:**
```yaml
1. Turn on receiver
2. Set input to Spotify
3. Wait 2 seconds
4. Spotify: PLAY_PAUSE
```

**Quick Volume Adjustment:**
```yaml
1. Spotify: VOLUME_DOWN
2. Spotify: VOLUME_DOWN
3. Spotify: VOLUME_DOWN
```

---

## 🔧 Configuration

### Polling Interval

Default: **30 seconds** (respects Spotify API rate limits)

To change (edit `config.json`):
```json
{
  "polling_interval": 30
}
```

Range: 10-300 seconds

### Docker Environment Variables
```bash
UC_CONFIG_HOME=/app/config          # Config directory
UC_INTEGRATION_INTERFACE=0.0.0.0    # Listen interface
UC_INTEGRATION_HTTP_PORT=9090       # HTTP port
UC_DISABLE_MDNS_PUBLISH=false       # mDNS discovery
```

---

## 🛠️ Troubleshooting

### Setup Issues

#### "Client ID not configured"
- ✅ Verify Client ID from Spotify Dashboard
- ✅ Check for extra spaces or characters
- ✅ Try copying again

#### "Authorization failed"
- ✅ Verify Client Secret is correct
- ✅ Ensure Redirect URI is **exactly** `https://example.com/callback`
- ✅ Check authorization code is complete
- ✅ Code expires quickly - restart if needed

#### Authorization Takes Long Time
- ⏱️ Spotify API rate limiting - normal behavior
- ⏱️ Can take 10-30 seconds to redirect
- ⏱️ Wait for "page not found" page
- ✅ Just be patient during authorization

#### Invalid Authorization Code
- ✅ Copy the full code (100+ characters)
- ✅ Can paste just code OR entire callback URL
- ✅ Don't include extra spaces
- ✅ Code is case-sensitive

### Runtime Issues

#### No Track Information
- ✅ Ensure Spotify is actively playing
- ✅ Check integration is authenticated
- ✅ Verify network connectivity
- ✅ Check logs for errors

#### Premium Features Not Working
- ✅ Verify you selected "Premium" during setup
- ✅ Confirm Spotify account is actually Premium
- ✅ Free users get display-only functionality
- ✅ Reconfigure if account upgraded

#### Commands Return Error But Work
- 🔧 **Fixed in v0.1.1** - Spotify API returns empty response
- 🔧 Commands execute successfully, error is cosmetic
- ✅ Update to latest version

#### Integration Shows ERROR State
- ✅ Check logs for authentication errors
- ✅ Token may have expired - reconfigure
- ✅ Verify Spotify Developer App is active
- ✅ Check network connectivity

### Docker Issues

#### Container Won't Start
- ✅ Check port 9090 is not in use
- ✅ Verify Docker has network access
- ✅ View logs: `docker logs uc-spotify`

#### Integration Not Discovered
- ✅ Ensure Remote and Docker on same network
- ✅ Check firewall settings
- ✅ Verify mDNS is working
- ✅ Try manual discovery with IP

#### Configuration Lost After Restart
- ✅ Verify volume is mounted correctly
- ✅ Check volume permissions
- ✅ Inspect volume: `docker volume inspect spotify-config`

---

## 📊 Technical Details

### Architecture
```
uc-intg-spotify/
├── uc_intg_spotify/
│   ├── __init__.py         # Version from driver.json
│   ├── driver.py           # Main integration driver
│   ├── client.py           # Spotify Web API client
│   ├── config.py           # Configuration management
│   ├── setup.py            # OAuth setup flow
│   ├── media_player.py     # Media player entity
│   └── remote.py           # Remote entity
├── driver.json             # Integration metadata
├── pyproject.toml          # Python project config
├── requirements.txt        # Dependencies
├── docker-compose.yml      # Docker deployment
└── Dockerfile              # Docker image
```

### API Integration

**Protocol:** HTTPS REST API  
**Authentication:** OAuth 2.0 Authorization Code Flow  
**Token Management:** Automatic refresh  
**Rate Limiting:** 30-second polling (configurable)

### Spotify API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/authorize` | OAuth authorization |
| `/api/token` | Token exchange/refresh |
| `/v1/me/player/currently-playing` | Get current track |
| `/v1/me/player` | Get playback state |
| `/v1/me/player/play` | Start playback |
| `/v1/me/player/pause` | Pause playback |
| `/v1/me/player/next` | Next track |
| `/v1/me/player/previous` | Previous track |
| `/v1/me/player/volume` | Set volume |

### Security

- ✅ OAuth 2.0 authentication
- ✅ Tokens stored locally only
- ✅ Client Secret filtered from logs
- ✅ SSL certificate validation
- ✅ User-owned credentials
- ✅ No data collection

---

## 🔒 Privacy & Security

### What This Integration Does

- ✅ Stores credentials **locally only**
- ✅ Communicates only with Spotify API
- ✅ No third-party data sharing
- ✅ You create and own the Developer App
- ✅ Tokens stored in local config file

### What This Integration Does NOT Do

- ❌ Does not share your credentials
- ❌ Does not store listening history
- ❌ Does not collect any user data
- ❌ Does not communicate with developer
- ❌ Does not require internet beyond Spotify API

### Your Responsibilities

- 🔐 Secure your Spotify Developer App credentials
- 📋 Comply with [Spotify Terms of Service](https://developer.spotify.com/terms)
- 🔄 Rotate credentials periodically (recommended)
- ⚠️ Use at your own risk

---

## 🧪 Development & Testing

### Run in Development Mode
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uc_intg_spotify.driver
```

### Debug with VSCode

Use provided `.vscode/launch.json`:
1. Open project in VSCode
2. Go to Run and Debug (Ctrl+Shift+D)
3. Select "Python: Spotify Integration"
4. Press F5

### Build Release
```bash
# Tag version
git tag v0.1.2
git push origin v0.1.2

# GitHub Actions builds automatically
# Creates .tar.gz and Docker image
```

---

## 🤝 Contributing

We welcome contributions!

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

### Areas for Contribution

- 🐛 Bug fixes
- ✨ Feature enhancements
- 📝 Documentation improvements
- 🌍 Translations
- 🧪 Tests

---

## 📄 License

This project is licensed under the **Mozilla Public License 2.0** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Credits

- **Developer:** [Meir Miyara](https://www.linkedin.com/in/meirmiyara/)
- **Framework:** [Unfolded Circle ucapi](https://github.com/unfoldedcircle/integration-python-library)
- **Community:** Unfolded Circle Discord and Forum members

---

## 📞 Support & Links

### Get Help

- 🐛 [GitHub Issues](https://github.com/mase1981/uc-intg-spotify/issues) - Report bugs
- 💬 [Discussions](https://github.com/mase1981/uc-intg-spotify/discussions) - Ask questions
- 👥 [UC Community Forum](https://community.unfoldedcircle.com/) - General support
- 💭 [Discord Server](https://discord.gg/zGVYf58) - Live chat

### Documentation

- 📖 [Spotify Web API](https://developer.spotify.com/documentation/web-api) - API reference
- 📚 [UC Developer Docs](https://github.com/unfoldedcircle/integration-python-library) - Integration API
- 🎓 [Setup Guide](https://github.com/mase1981/uc-intg-spotify/wiki) - Detailed instructions

### Related Projects

- 🎵 [UC Spotify Integration](https://github.com/mase1981/uc-intg-spotify) - This project
- 📺 [Fire TV Integration](https://github.com/mase1981/uc-intg-firetv) - Amazon Fire TV
- 🔊 [WiiM Integration](https://github.com/mase1981/uc-intg-wiim) - WiiM Audio
- 🏠 [LG Horizon Integration](https://github.com/mase1981/uc-intg-horizon) - Set-top boxes

---

## ⚠️ Legal Disclaimers

### Third-Party Service Integration

This integration is an **independent, unofficial project** that interfaces with Spotify's publicly available Web API:

- ❌ **NOT** sponsored, endorsed, or affiliated with Spotify AB
- ❌ **NOT** an official Spotify product or service
- ✅ Developed independently using Spotify's public API
- ✅ Open source under MPL-2.0 license

### Intellectual Property

- **Spotify** is a registered trademark of Spotify AB
- All Spotify-related trademarks and logos are property of Spotify AB
- This project claims no ownership of Spotify intellectual property
- Album artwork and track information accessed via API remain property of copyright holders

### Terms of Service

By using this integration, you agree to:

- ✅ Comply with [Spotify Developer Terms](https://developer.spotify.com/terms)
- ✅ Comply with [Spotify Web API Terms](https://developer.spotify.com/terms)
- ✅ Create and manage your own Spotify Developer App
- ✅ Accept responsibility for your API usage
- ✅ Use at your own risk

### Liability & Warranty

- ⚠️ **No warranty provided** - software provided "as is"
- ⚠️ Developer not liable for account restrictions or consequences
- ⚠️ You are responsible for securing your credentials
- ⚠️ You are responsible for compliance with Spotify policies

### Data Privacy

- 🔒 Integration does not collect user data
- 🔒 Authentication tokens stored locally only
- 🔒 No data transmitted to third parties
- 🔒 Credentials remain on your device
- 📋 Review [Spotify Privacy Policy](https://www.spotify.com/privacy) for API data handling

**For questions about Spotify services, terms, or policies, contact Spotify directly.**

---

<div align="center">

Made with ❤️ by [Meir Miyara](https://www.linkedin.com/in/meirmiyara/)

⭐ Star this repo if you find it useful!

[Report Bug](https://github.com/mase1981/uc-intg-spotify/issues) · [Request Feature](https://github.com/mase1981/uc-intg-spotify/issues) · [Discussions](https://github.com/mase1981/uc-intg-spotify/discussions)

**Version:** 0.1.1 | **Updated:** November 2024

</div>
