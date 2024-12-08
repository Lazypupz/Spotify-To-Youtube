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
import sp


class YoutubeAPI:
    SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']



    def __init__(self):
        self.creds = None
        self.service = None
        self.token_file = 'token.pickle'
        self.credentials_file = 'credentials.json'
        self.video_cache = {}
        self.playlist_cache = {}

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

    def get_existing_playlists(self):
        #Retrieve and cache the user YouTube playlists.
        request = self.service.playlists().list(
            part='snippet',
            mine=True,
            maxResults=50
        )
        response = request.execute()
        self.playlist_cache = {item['snippet']['title']: item['id'] for item in response['items']}
        return self.playlist_cache

    def check_playlist_exists(self, playlist_name):
        #Check if a Youtube playlist with the name exists.
        if not self.playlist_cache:
            self.get_existing_playlists()
        return playlist_name in self.playlist_cache       

    def print_pcache(self):
        if not self.playlist_cache:
            self.get_existing_playlists()
        print("The current playlists are: \n")
        for playlist_name in self.playlist_cache.keys():
            print(playlist_name)
            return None

    def del_playlist(self, playlist_id, playlist_name):
        if not self.playlist_cache:
            self.get_existing_playlists()
        if playlist_id not in self.playlist_cache.values():
            print("Playlist ID not found in cache")
            return None
        try:
            request = self.service.playlists().delete(
                id=playlist_id
            )
            response = request.execute()
            print(f"Playlist '{playlist_name}' was deleted")        
        except Exception as e:
            print("Error occurred:", e)





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
        return response['id']  # Return the ID of the newly made playlist

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
                print(f"Video {sp.Spotify.get_playlists().playlist_tracks} added to playlist {playlist_id}.")
                return response  # Return if successful

            except HttpError as e:
                if e.resp.status in [409]:  # Check for specific errors
                    print(f"Conflict error (409): {e}. Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"An error occurred: {e}")
                    break  # Exit on other errors

        print("Failed to add video after multiple attempts.")

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

