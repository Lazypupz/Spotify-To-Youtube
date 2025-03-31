import requests
from dotenv import load_dotenv
import os
import urllib.parse
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import time
from googleapiclient.errors import HttpError

load_dotenv()

class Spotify:
    def __init__(self):
        self.client_id = os.getenv('SPOTIFYCLIENT_ID')
        self.client_secret = os.getenv('SPOTIFYCLIENT_SECRET')
        self.REDIRECT_URI = 'http://localhost:5000/callback'
        self.AUTH_URL = "https://accounts.spotify.com/authorize"
        self.TOKEN_URL = "https://accounts.spotify.com/api/token"
        self.API_BASE_URL = "https://api.spotify.com/v1/"
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None

    def login(self):
        scope = "user-read-private user-read-email playlist-read-private playlist-read-collaborative"
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': scope,
            'redirect_uri': self.REDIRECT_URI,
            'show_dialog': True
        }
        ## parsing query
        parsedQuery = urllib.parse.urlencode(params)
        auth_url = f"{self.AUTH_URL}?{parsedQuery}"

        print(f"Please go to this URL and authorize the app (you have 20 seconds):\n {auth_url}\n")
        print("Authenticating Log-in")

        code = ("Enter Code from URL (everything after ?=): ")
        self.get_token(code)

    def get_token(self, code):
        req_body = {
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.REDIRECT_URI,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        response = requests.post(self.TOKEN_URL, data=req_body)
        token_info = response.json()
        self.access_token = token_info.get('access_token')
        self.refresh_token = token_info.get('refresh_token')
        self.expires_at = datetime.now().timestamp() + token_info.get('expires_in', 0)
        if not self.access_token:
            print("Failed to gain access token.")
            return

    def get_User_Name(self):
        if not self.access_token:
            print("Log-in first")
            return None
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(self.API_BASE_URL + "me", headers=headers)
        user_data = response.json()
        return user_data.get('display_name', 'Unknown Name')

    def get_playlists(self):
        if not self.access_token:
            print("You need to log in first.")
            return []
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(self.API_BASE_URL + 'me/playlists', headers=headers)
        playlists = response.json()
        if 'items' not in playlists:
            print("Error grabbing playlists")
            return []

        playlist_tracks = []
        for playlist in playlists['items']:
            playlist_id = playlist['id']
            playlist_name = playlist['name']
            tracks_response = requests.get(self.API_BASE_URL + f'playlists/{playlist_id}/tracks', headers=headers)
            tracks = tracks_response.json()
            tracks_info = [
                {
                    'name': track['track']['name'],
                    'artist': ', '.join(artist['name'] for artist in track['track']['artists']),
                    'duration': f"{track['track']['duration_ms'] // 60000}:{(track['track']['duration_ms'] % 60000) // 1000:02}"
                }
                for track in tracks.get('items', []) if track['track'] and 'duration_ms' in track['track']
            ]
            playlist_tracks.append({'playlist_name': playlist_name, 'tracks': tracks_info})

        return playlist_tracks