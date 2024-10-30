from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
import csv
load_dotenv()
#recieves keys fron .env file
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')


AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'


#is any errors happen the user is redirected here
REDIRECT_URI = 'http://localhost:5000/callback'



#request access token
def get_token():
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    result = post(url, headers=headers, data=data)
    json_result = result.json()
    token = json_result["access_token"]
    return token



#searchs for a playlist and displays the song names of each one
def search_playlist(token, playlist_name):
    url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {
        "q": playlist_name,
        "type": "playlist",
        "limit": 1 
    }
    
    result = get(url, headers=headers, params=params)
    json_result = result.json()
    
    
    playlist_id = json_result['playlists']['items'][0]['id']


    tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    tracks_result = get(tracks_url, headers=headers)
    tracks_json = tracks_result.json()
    plylist_names = []
    for item in tracks_json['items']:
        track_name = item['track']['name']
        print(track_name)
        
        plylist_names.append([track_name])
    
    with open ('tracks.csv', 'w', newline='')as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(plylist_names)


token = get_token()
the_name =  str(input("What is the name of the playlist?: "))
id_playlist = search_playlist(token, the_name)
