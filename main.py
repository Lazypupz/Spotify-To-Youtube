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
        auth_url = f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"
        print(f"Please go to this URL and authorize the application: {auth_url}")
        code = input("Enter the code from the URL: ")
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
        self.access_token = token_info['access_token']
        self.refresh_token = token_info['refresh_token']
        self.expires_at = datetime.now().timestamp() + token_info['expires_in']
        print("Access token obtained successfully.")
    
    def get_User_Name(self):
        if self.access_token is None:
            print("Log-in first")
            return None
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        response = requests.get(self.API_BASE_URL + "me", headers=headers)
        user_name = response.json()

        return user_name.get('display_name', 'Unknown Name')

    def get_playlists(self):
        if self.access_token is None:
            print("You need to log in first.")
            return []

        if datetime.now().timestamp() > self.expires_at:
            print("Access token expired. Please log in again.")
            return []

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        response = requests.get(self.API_BASE_URL + 'me/playlists', headers=headers)
        playlists = response.json()

        playlist_tracks = []
        for playlist in playlists['items']:
            playlist_id = playlist['id']
            playlist_name = playlist['name']
            tracks_response = requests.get(self.API_BASE_URL + f'playlists/{playlist_id}/tracks', headers=headers)
            tracks = tracks_response.json()

            tracks_info = [
                {
                    'name': track['track']['name'],
                    'artist': ', '.join(artist['name'] for artist in track['track']['artists']),  # Get the artist names
                    'duration': f"{track['track']['duration_ms'] // 60000}:{(track['track']['duration_ms'] % 60000) // 1000:02}"
                }
                for track in tracks['items'] if track['track'] and 'duration_ms' in track['track']
            ]

            playlist_tracks.append({
                'playlist_name': playlist_name,
                'tracks': tracks_info
            })

        return playlist_tracks  # Ensure this returns a list

class YoutubeAPI:
    SCOPES = ['https://www.googleapis.com/auth/youtube']

    def __init__(self):
        self.creds = None
        self.service = None
        self.token_file = 'token.pickle'
        self.credentials_file = 'credentials.json'
        self.video_cache = {}

    def authenticate(self):
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                self.creds = flow.run_local_server(port=8080)

            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('youtube', 'v3', credentials=self.creds)

    def create_playlist(self, playlist_name):
        request = self.service.playlists().insert(
            part='snippet,status',
            body={
                'snippet': {
                    'title': playlist_name,
                    'description': 'Playlist created from Spotify',
                    'tags': ['spotify', 'youtube'],
                    'defaultLanguage': 'en'
                },
                'status': {
                    'privacyStatus': 'public'
                }
            }
        )
        response = request.execute()
        return response['id']  # Return the ID of the newly created playlist

    def search_video(self, song_name, artist_name):

        cache_key = f"{song_name} - {artist_name}"
        query = f"{song_name} {artist_name}"
        if cache_key in self.video_cache:
            print(f"Using cached videoID for {cache_key}")
            return self.video_cache[cache_key];
        request = self.service.search().list(
            part='snippet',
            q=query,
            type='video',
            maxResults=1
        )
        response = request.execute()
        if response['items']:
            video_id = response['items'][0]['id']['videoId']
            self.video_cache[cache_key] = video_id
            return video_id
        return None

    def add_video_to_playlist(self, playlist_id, video_id):
        request_body = {
            'snippet': {
                'playlistId': playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id
                }
            }
        }

        for attempt in range(5):
            try:
                request = self.service.playlistItems().insert(
                    part='snippet',
                    body=request_body
                )
                response = request.execute()
                print(f"Video {video_id} added to playlist {playlist_id}.")
                return response  # Return if successful

            except HttpError as e:
                if e.resp.status in [409]:  # Check for specific errors
                    print(f"Conflict error (409): {e}. Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"An error occurred: {e}")
                    break  # Exit on other errors

        print("Failed to add video after multiple attempts.")
        import time

        for attempt in range(5):
            try:
                response = request.execute()
                break
            except HttpError as e:
                if e.resp.status == 403 and 'quota' in str(e):
                    print(f"Quota exceeded. Attempt {attempt + 1} of 5.")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"An error occurred: {e}")
                    break

def main():

    print("Welcome To Spotify-to-Youtube app from Lazypupz")
    print("Please make sure you have the necessary API keys and authentication set up.")
    
    spotify = Spotify()
    spotify.login()  # Log in to get the access token
    playlists = spotify.get_playlists()  # Grab playlistss

    # Check if playlists were fetched successfully
    if not playlists:
        print("No playlists were found or an error occurred.")
        return
    user_name = spotify.get_User_Name()
    # Display user's playlists
    print(f"Available Spotify Playlists for {user_name}:")
    for i, playlist in enumerate(playlists):
        print(f"{i + 1}: {playlist['playlist_name']}")

    # User Input for playlist choice
    choice = int(input("Select a playlist to convert to YouTube: ")) - 1
    if choice < 0 or choice >= len(playlists):
        print("Invalid choice. Exiting.")
        return

    selected_playlist = playlists[choice]
    playlist_name = selected_playlist['playlist_name']
    print(f"Creating YouTube playlist: {playlist_name}")

    youtube_api = YoutubeAPI()
    youtube_api.authenticate()  

    playlist_id = youtube_api.create_playlist(playlist_name)

    # Add each track to the Youtube playlist
    for track in selected_playlist['tracks']:
        song_name = track['name']
        artist_name = track['artist']  # Get the artists name
        print(f"Searching for video for: {song_name} by {artist_name}")
        video_id = youtube_api.search_video(song_name, artist_name)  # Pass both song and artist
        if video_id:
            print(f"Adding {song_name} to playlist.")
            youtube_api.add_video_to_playlist(playlist_id, video_id)
            time.sleep(1)   
        else:
            print(f"No video found for {song_name}  {artist_name}.")

if __name__ == '__main__':
    main()

