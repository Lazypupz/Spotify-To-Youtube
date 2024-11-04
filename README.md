# Spotify-to-YouTube Playlist Converter

This is a console application that allows users to convert their Spotify playlists into YouTube playlists. This can be helpful for users who want to watch music videos on YouTube based on their Spotify playlists.

## Features

- **Playlist Conversion:** Converts Spotify playlists to YouTube playlists with a single command.
- **Easy Authentication:** Supports Spotify and YouTube API authentication.
- **Automated Matching:** Finds matching songs on YouTube based on Spotify track data.
- **CLI Interface:** Simple command-line interface for quick and easy use.
- **Error Handling:** Provides informative feedback for any errors during the conversion process.
- **Accurate:** You will get the correct songs majority of the time.

## Prerequisites

Before running this application, ensure you have the following:

- **Python 3.9+** installed on your system.
- **Spotify Developer Account** and an active application for Spotify API access.
- **YouTube Data API v3** enabled on a Google Cloud project.

##Setup
##1. Clone the Repository
```bash
cd C:\Users\{your_name}\Spotify-To-Youtube
```
##2. Install required dependencies
Install the required packages listed in *requirements.txt*:
```bash
pip install -r requirements.txt
```
##3. Spotify API Setup
- **Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)**
- **Create a new application and get your Client ID and Client Secret**
- ** Add these details to a .env file in the root directory of the project**
```txt
SPOTIFYCLIENT_ID = "your_spotify_client_id"
SPOTIFYCLIENT_SECRET = "your_spotify_client_secret"
```
##4. Youtube API Setup
- **Go to the [Google Cloud Console](https://console.cloud.google.com/)**
- **Create a project**
- **Enable the ***Youtube Data API v3 *** for your project**
- **Create OAuth 2.0 credentials and download the JSON file**
- Save this JSON file in the root dir as *credentials.json*

##Usage
##**Converting a Playlist**
- Run the following command to start the application
  ```bash
  python main.py
  ```
- You will be told to Enter the spotify playlist URL and then authorize access to both spotify and youtube accounts.
- One authorized the app will search for each song from the Spotify playlist on Youtube and create a new youtube playlist with matching songs
##**Command Line Input**
- Follow the instructions on the console
- Chose what playlist to convert


**Keep in mind that sometimes the wrong song may be converted.

