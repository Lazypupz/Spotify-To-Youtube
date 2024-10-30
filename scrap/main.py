from dotenv import load_dotenv
import os
import base64
import requests
import csv

# Load environment variables
load_dotenv()
client_id = os.getenv('SPOTIFYCLIENT_ID')
client_secret = os.getenv('SPOTIFYCLIENT_SECRET')

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

# Redirect URI for any errors
REDIRECT_URI = 'http://localhost:5000/callback'

# Request access token
def get_token():
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    url = TOKEN_URL
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    result = requests.post(url, headers=headers, data=data)
    result.raise_for_status()  # Raise an error for bad responses
    json_result = result.json()
    return json_result["access_token"]

# Fetch tracks from a playlist
def get(url, headers, params=None):
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise an error for bad responses
    return response

def search_playlist(token, playlist_id):
    url = f"{API_BASE_URL}playlists/{playlist_id}/tracks"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Fetch tracks from the specified playlist ID
    tracks_result = get(url, headers=headers)
    tracks_json = tracks_result.json()
    
    playlist_names = []
    for item in tracks_json.get('items', []):
        track_name = item.get('track', {}).get('name', 'Unknown Track')
        print(track_name)
        playlist_names.append([track_name])
    
    # Create a CSV file with the songs in the playlist
    with open('tracks.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(playlist_names)

# Main code
if __name__ == "__main__":
    token = get_token()
    id_playlist = input("What is the playlist ID?: ")
    search_playlist(token, id_playlist)