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
        print(f"Please go to this URL and authorize the app: {auth_url}\n")
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
    print("Please make sure you have your own personal API keys and authentication set up in the README on Github (*required*).")

    spotify = Spotify()
    spotify.login()
    playlists = spotify.get_playlists()


    youtube_api = YoutubeAPI()
    youtube_api.authenticate()

    while True:
        option = input("(1) Add a playlist, (2) Delete a playlist, (3) Display Spotify Playlists, (4) Display Youtube Playlist, (5) Exit: ")
        if option not in ["1", "2", "3", "4", "5"]:
            print("Can't do that m8 - Please enter 1, 2, 3, 4, 5")
            continue

        if option == "1":

            choice = select_playlist(playlists)

            if choice is None:
                print("Invalid choice.")
                return

            selected_playlist = playlists[choice]
            playlist_name = selected_playlist['playlist_name']
            print(f"Converting Spotify playlist '{playlist_name}' to YouTube...")

            playlist_id = youtube_api.create_playlist(playlist_name)
            for track in selected_playlist['tracks']:
                video_id = youtube_api.search_video(track['name'], track['artist'])
                if video_id:
                    youtube_api.add_video_to_playlist(playlist_id, video_id)
                    time.sleep(1)
                else:
                    print(f"No video found for {track['name']} by {track['artist']}.")

        elif option == "2":
            youtube_api = YoutubeAPI()
            youtube_api.authenticate()
            choice = select_playlist(playlists)

            if choice is None:
                print("Invalid choice.")
                return

            selected_playlist = playlists[choice]
            playlist_name = selected_playlist['playlist_name']
            print(f"Checking if YouTube playlist '{playlist_name}' exists...")

            if youtube_api.check_playlist_exists(playlist_name):
                playlist_id = youtube_api.playlist_cache[playlist_name]
                youtube_api.del_playlist(playlist_id, playlist_name)
            else:
                print(f"No YouTube playlist found with the name '{playlist_name}'.")
            
        elif option == "3":
            user_name = spotify.get_User_Name()
            print(f"Available Spotify Playlists for {user_name}:")
            for i, playlist in enumerate(playlists):
                print(f"{i + 1}: {playlist['playlist_name']}")
        
        elif option == "4":
            youtube_api.print_pcache()
        elif option == "5":
            print("Exiting now.......")
            break



def select_playlist(playlists):
    try:
        choice = int(input("Select a playlist by number: ")) - 1
        if 0 <= choice < len(playlists):
            return choice
        else:
            print("Invalid choice. Please select a valid playlist number.")
            return None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None
if __name__ == '__main__':
    main()

