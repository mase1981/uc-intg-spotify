# Spotify Integration for Unfolded Circle Remote Two

This integration allows you to control Spotify playback and view currently playing track information on your Unfolded Circle Remote Two/Three.

**NOTE:** This integration require some additional steps, you need to be comfortable with it. I simplified as much as i could, read this document carefully and you should be able to get this done fairely easily. Thank You: Meir Miyara :smiley:
## Features

### For All Users
- Display currently playing track information (title, artist, album, artwork)
- Real-time playback progress
- Track duration display
- Album artwork display

### For Spotify Premium Users
- Play/pause control
- Next/previous track navigation
- Volume control
- Physical button mapping for playback controls

## Prerequisites

1. Unfolded Circle Remote Two/3
2. Spotify account (Premium recommended for full functionality)
3. **Spotify Developer App** (see setup below)

## Spotify Developer App Setup

**IMPORTANT:** Before installing this integration, you must create a Spotify Developer App to get your own Client ID and Client Secret.

### Step 1: Create Spotify Developer App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create App"**
4. Fill in the details:
   - **App Name:** `UC Remote Integration` (or any name you prefer)
   - **App Description:** `Unfolded Circle Remote integration`
   - **Redirect URI:** `https://example.com/callback` ⚠️ **Must be exactly this**
   - **API:** Check **"Web API"**
5. Click **"Save"**
6. On your app's dashboard, note down:
   - **Client ID** (visible immediately)
   - **Client Secret** (click "Show Client Secret" to reveal)

### Step 2: Important Notes

- **Keep your credentials secure** - Don't share your Client ID and Client Secret
- **Redirect URI must be exact** - Use `https://example.com/callback` exactly
- **Free vs Premium** - The integration works with both, but Premium gets playback controls

## Installation

**NOTE:** During installation once you click log in to your spotify account: it might take some time for it to log in and redict to the empty page - this is expected and due to Spotify API rate. 

### Method 1: Pre-built Release (Recommended)
1. Download the latest `.tar.gz` file from the [Releases](https://github.com/mase1981/uc-intg-spotify/releases) page
2. Upload to your Remote Two via the web configurator
3. Follow the setup process

### Method 2: Development Installation
1. Clone this repository
2. Set up your development environment (see Development section)

### Method 3: Docker Deployment

You can run the Spotify integration as a Docker container for easy deployment and management.

#### Prerequisites for Docker
1. Docker and Docker Compose installed
2. Your Remote Two on the same network as the Docker host

#### Quick Start with Docker Compose

1. **Create a directory for the integration:**
   ```bash
   mkdir uc-spotify-integration
   cd uc-spotify-integration
   ```

2. **Download the docker-compose.yml file (choose one method):**

   **Option A - Direct download:**
   ```bash
   wget https://raw.githubusercontent.com/mase1981/uc-intg-spotify/main/docker-compose.yml
   ```

   **Option B - Using curl:**
   ```bash
   curl -o docker-compose.yml https://raw.githubusercontent.com/mase1981/uc-intg-spotify/main/docker-compose.yml
   ```

   **Option C - Create manually:**
   Create a file named `docker-compose.yml` with the following content:
   ```yaml
   version: '3.8'

   services:
     spotify-integration:
       build: .
       # Uncomment the next line to use pre-built image instead of building
       # image: mase1981/uc-intg-spotify:latest
       container_name: uc-spotify-integration
       restart: unless-stopped
       
       # Network configuration for mDNS discovery
       network_mode: host
       
       # Environment variables (only technical settings)
       environment:
         - UC_CONFIG_HOME=/app/config
         - UC_INTEGRATION_INTERFACE=0.0.0.0
         - UC_INTEGRATION_HTTP_PORT=9090
         # Uncomment to disable mDNS publishing if needed
         # - UC_DISABLE_MDNS_PUBLISH=true
       
       # Volume for persistent configuration
       volumes:
         - spotify-config:/app/config
       
       # Health check
       healthcheck:
         test: ["CMD-SHELL", "curl -f http://localhost:9090/ || exit 1"]
         interval: 30s
         timeout: 10s
         retries: 3
         start_period: 30s
       
       # Logging configuration
       logging:
         driver: "json-file"
         options:
           max-size: "10m"
           max-file: "3"

   volumes:
     spotify-config:
       driver: local
   ```

3. **If using the pre-built image, edit the docker-compose.yml:**
   ```bash
   # Comment out the build line and uncomment the image line
   sed -i 's/build: ./#build: ./' docker-compose.yml
   sed -i 's/# image: mase1981/image: mase1981/' docker-compose.yml
   ```

4. **Start the container:**
   ```bash
   docker-compose up -d
   ```

5. **Check logs:**
   ```bash
   docker-compose logs -f spotify-integration
   ```

6. **Configure via Remote Two:**
   - Open your Remote Two web configurator
   - The integration should be auto-discovered via mDNS
   - Follow the normal setup process:
     - Enter your Spotify Developer App credentials
     - Complete OAuth authentication
     - Entities will be created automatically

#### Manual Docker Run (Alternative)

```bash
docker run -d \
  --name uc-spotify-integration \
  --network host \
  -v spotify-config:/app/config \
  --restart unless-stopped \
  mase1981/uc-intg-spotify:latest
```

#### Docker Setup Process

1. **Start the container** - No environment variables needed
2. **Discover the integration** on your Remote Two via the web configurator
3. **Complete setup through Remote Two:**
   - Enter your Spotify Developer App Client ID and Secret
   - Select if you have Spotify Premium
   - Complete OAuth authentication flow
   - Configuration is automatically saved to the Docker volume
4. **Entities will be created** and ready to use

#### Docker Management

**View logs:**
```bash
docker-compose logs -f spotify-integration
```

**Restart the container:**
```bash
docker-compose restart spotify-integration
```

**Update to latest version:**
```bash
docker-compose pull
docker-compose up -d
```

**Stop and remove:**
```bash
docker-compose down
```

**Reset configuration (start fresh setup):**
```bash
docker-compose down
docker volume rm uc-spotify-integration_spotify-config
docker-compose up -d
```

#### Docker Volumes

The container uses a named volume `spotify-config` to persist:
- OAuth tokens
- User preferences  
- Spotify app credentials
- Integration configuration

This ensures your setup persists across container restarts and updates.

#### Docker Networking

The integration uses host networking for:
- **mDNS discovery** - Auto-discovery by Remote Two
- **WebSocket communication** - Direct connection from Remote Two
- **No port mapping needed** - Integration available at `http://docker-host:9090`

#### Docker Troubleshooting

**Container won't start:**
- Check Docker logs: `docker-compose logs spotify-integration`
- Verify port 9090 is not already in use
- Ensure Docker has network access

**Integration not discovered by Remote Two:**
- Ensure Remote Two and Docker host are on the same network
- Check firewall settings on Docker host
- Verify mDNS/Bonjour is working on your network
- Try manual discovery using the Docker host IP

**Setup fails:**
- Check container logs during setup process
- Verify your Spotify app redirect URI is exactly: `https://example.com/callback`
- Ensure your Spotify Developer App credentials are correct

**Configuration lost after restart:**
- Verify the Docker volume is properly mounted
- Check volume permissions: `docker volume inspect uc-spotify-integration_spotify-config`

**docker-compose.yml download issues:**
- Try alternative download methods shown above
- Verify your internet connection
- Check if GitHub is accessible from your network
- Use manual creation method if download fails

## Setup Process

### During Integration Setup:

1. **App Credentials Page:**
   - Enter your **Spotify Client ID** from the developer dashboard
   - Enter your **Spotify Client Secret** from the developer dashboard  
   - Select whether you have **Spotify Premium**
   - Click **Next**

2. **Authentication Page:**
   - Click the provided Spotify authorization URL
   - Log into your Spotify account and authorize the app
   - Your browser will show "page not found" - **this is normal!**
   - Copy the authorization code from your browser's address bar
   - Paste it into the setup form
   - Click **Finish**

3. **Completion:**
   - Two entities will be created:
     - **Spotify Player** (Media Player entity)
     - **Spotify Remote** (Remote entity with playback controls)

## Usage

### Media Player Entity
- Shows currently playing track information
- Displays album artwork
- Shows playback progress
- Premium users get playback control buttons

### Remote Entity  
- Physical button mappings for Premium users
- Custom UI with playback controls
- Synchronized state with Spotify playback

## Troubleshooting

### Common Issues

1. **"Client ID not configured" error:**
   - Verify you entered the correct Client ID from your Spotify app
   - Make sure there are no extra spaces or characters

2. **"Authorization failed" error:**
   - Check that your Client Secret is correct
   - Ensure your Redirect URI is exactly `https://example.com/callback`
   - Verify your Spotify app is not in "Development Mode" restrictions

3. **Premium Features Not Working:**
   - Verify you selected "Premium User" during setup
   - Ensure your Spotify account actually has Premium status
   - Non-Premium users will get display-only functionality

4. **No Track Information:**
   - Make sure Spotify is actively playing on one of your devices
   - Check that the integration has valid authentication tokens
   - Verify network connectivity

### Setup Issues

1. **Invalid Client ID/Secret:**
   - Double-check credentials from your Spotify Developer Dashboard
   - Ensure no extra characters or spaces were copied

2. **Authorization Code Issues:**
   - Make sure you're copying the full code from the URL
   - You can paste either just the code or the entire callback URL
   - The code is usually quite long (100+ characters)

### Logs

Check the Remote Two logs for detailed error information:
- Authentication issues
- API rate limiting
- Network connectivity problems

## Development

### Setup Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mase1981/uc-intg-spotify.git
   cd uc-intg-spotify
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run in development mode:**
   ```bash
   python uc_intg_spotify/driver.py
   ```

### Project Structure

```
uc-intg-spotify/
├── uc_intg_spotify/
│   ├── __init__.py
│   ├── driver.py          # Main integration driver
│   ├── client.py          # Spotify API client
│   ├── config.py          # Configuration management
│   ├── setup.py           # OAuth setup handler
│   ├── media_player.py    # Media player entity
│   └── remote.py          # Remote entity
├── .vscode/
│   └── launch.json        # VSCode debug configuration
├── .github/
│   └── workflows/
│       └── build.yml      # GitHub Actions build
├── driver.json            # Integration metadata
├── config.json            # Runtime configuration (created during setup)
├── pyproject.toml         # Python project configuration
├── requirements.txt       # Python dependencies
└── README.md
```

### Debugging

Use VSCode with the provided `launch.json` configuration:
1. Open the project in VSCode
2. Go to Run and Debug (Ctrl+Shift+D)
3. Select "Python: Spotify Integration"
4. Press F5 to start debugging

The integration will start on `http://localhost:9090` and publish via mDNS.

### Key Implementation Notes

1. **No Hardcoded Credentials**: All Spotify app credentials come from user setup
2. **Secure Storage**: Client secrets are stored in local config but filtered from logs
3. **Premium Detection**: Setup flow includes Premium user detection to enable/disable features
4. **Token Management**: Automatic OAuth token refresh handling
5. **Error Handling**: Proper StatusCodes.OK for unsupported operations to avoid UI errors

## API Rate Limiting

The integration polls Spotify's API every 30 seconds by default to respect rate limits:
- Normal operation: 30-second intervals
- Standby mode: 120-second intervals  
- No polling when no entities are subscribed

## Security Notes

- **Your Spotify app credentials stay on your local device**
- **No credentials are shared with the integration author**
- **Each user creates their own Spotify Developer App**
- **Client Secret is stored locally but filtered from debug logs**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

**Developer:** Meir Miyara (meir.miyara@gmail.com)
**GitHub:** https://github.com/mase1981

## License

This project is licensed under the Mozilla Public License 2.0 - see the LICENSE file for details.

## Legal Disclaimers

### Third-Party Service Integration
This integration is an independent, unofficial project that interfaces with Spotify's publicly available Web API. This project is:

- **NOT sponsored, endorsed, or affiliated** with Spotify AB or any of its subsidiaries
- **NOT an official Spotify product** or service
- Developed independently using Spotify's public Web API documentation

### Intellectual Property
- **Spotify** is a trademark of Spotify AB
- All Spotify-related trademarks, service marks, and logos are the property of Spotify AB
- This project claims no ownership of Spotify's intellectual property
- Album artwork, track information, and other content accessed through the API remain the property of their respective copyright holders

### API Usage and Terms
- Users must comply with [Spotify's Developer Terms of Service](https://developer.spotify.com/terms)
- Users must comply with [Spotify's Web API Terms of Use](https://developer.spotify.com/terms)
- This integration requires users to create their own Spotify Developer App
- Usage of this integration is subject to Spotify's rate limiting and API policies

### User Responsibilities
By using this integration, you acknowledge that:

- You are responsible for creating and managing your own Spotify Developer App
- You are responsible for complying with all applicable terms of service
- You use this software at your own risk
- You are responsible for securing your own Spotify app credentials
- The developer is not liable for any account restrictions, suspensions, or other consequences

### Data and Privacy
- This integration does not store, collect, or transmit personal data beyond what is necessary for API functionality
- Authentication tokens are stored locally on your device
- No user data is shared with third parties
- Spotify app credentials remain on your local device
- Users should review Spotify's privacy policy for information about data handled by Spotify's services

**For questions about Spotify's services, terms, or policies, please contact Spotify directly.**

## Support

- GitHub Issues: [Report bugs and request features](https://github.com/mase1981/uc-intg-spotify/issues)
- Unfolded Circle Community: [Get help from the community](https://unfoldedcircle.com/community)

## Acknowledgments

- Unfolded Circle for the Remote Two/3 and integration API
- Spotify for their comprehensive Web API
- The UC community for testing and feedback
- I Really do hope you will enjoy this integraion - Thank you again: **Meir Miyara**