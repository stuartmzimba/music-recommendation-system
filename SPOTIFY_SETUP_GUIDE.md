# 🎵 **Complete Spotify App Setup Guide (2025 Updated)**

## **📋 New Spotify Requirements (April 2025)**

⚠️ **Important Changes:**
- **NO** `localhost` allowed as redirect URI
- **MUST** use explicit IP addresses for loopback
- **HTTPS required** except for loopback addresses
- **Exact match** required for redirect URIs

---

## **Step 1: Go to Spotify Developer Dashboard**

1. Open your web browser
2. Navigate to: **https://developer.spotify.com/dashboard**
3. You'll see the Spotify for Developers homepage

## **Step 2: Log In to Spotify**

1. Click **"Log In"** in the top right corner
2. Enter your Spotify account credentials
   ```markdown
   # 🎵 Spotify App Setup Guide (updated)

   This guide walks you through creating a Spotify developer app and configuring credentials for use with the project.

   ## Quick checklist
   - Add redirect URI: `http://127.0.0.1:8080/callback`
   - Obtain Client ID and Client Secret
   - Supply credentials via `setup_spotify.py`, environment variables, or a `.env` file

   ## Steps

   1. Open the Spotify Developer Dashboard: https://developer.spotify.com/dashboard
   2. Log in and click "Create App". Fill the app name/description as you like (e.g. "Music Recommender System").
   3. In the app settings, add the redirect URI exactly as:

   ```
   http://127.0.0.1:8080/callback
   ```

   Note: Spotify no longer accepts `localhost` as the literal in redirect URIs for some workflows — use the explicit loopback IP `127.0.0.1` (or `::1` for IPv6).

   4. Copy the Client ID and Client Secret from the app page. Keep the secret private.

   ## Provide credentials to the project
   Choose one of these methods:

   - Recommended: run the interactive setup script which stores credentials in `.env`:

   ```powershell
   python bin/setup_spotify.py
   ```

   - Environment variables (temporary in PowerShell):

   ```powershell
   $env:SPOTIFY_CLIENT_ID = "your_client_id"
   $env:SPOTIFY_CLIENT_SECRET = "your_client_secret"
   ```

   - Create a `.env` file in the project root with:

   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   ```

   ## Test fetching
   Run a small fetch to verify credentials and saving of results:

   ```powershell
   python fetchers/spotify_simple_fetcher.py
   ```

   If the fetch succeeds you should see files saved into `data/sample/`, e.g. `spotify_fetched_songs.csv`.

   ## Troubleshooting
   - Invalid redirect URI: ensure you added `http://127.0.0.1:8080/callback` exactly in the Spotify app settings.
   - Invalid client/secret: ensure there are no extra spaces and that you copied them correctly.
   - Rate limits: Spotify rate limits apply (few hundred requests/minute depending on endpoint). Back off on repeated failures.

   ## Next steps
   - After fetching, reload data with `python tools/reload_data.py` and then run the app launcher as described in the README.

   ```
   - Save it somewhere safe
