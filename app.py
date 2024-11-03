from flask import Flask, redirect, request, jsonify, session, render_template
import requests
from dotenv import load_dotenv
import os
import urllib.parse
from datetime import datetime

app = Flask(__name__)
load_dotenv()

class Spotify:
    
    def __init__(self):
        app.secret_key = os.getenv("flask_key")
        self.client_id = os.getenv('SPOTIFYCLIENT_ID')
        self.client_secret = os.getenv('SPOTIFYCLIENT_SECRET')
        self.REDIRECT_URI = 'http://localhost:5000/callback'
        self.AUTH_URL = "https://accounts.spotify.com/authorize"
        self.TOKEN_URL = "https://accounts.spotify.com/api/token"
        self.API_BASE_URL = "https://api.spotify.com/v1/"

    def index(self):
        return render_template('index.html')

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
        return redirect(auth_url)

    def callback(self):
        if 'error' in request.args:
            return jsonify({'error': request.args['error']})

        if 'code' in request.args:
            req_body = {
                'code': request.args['code'],
                'grant_type': 'authorization_code',
                'redirect_uri': self.REDIRECT_URI,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }

            response = requests.post(self.TOKEN_URL, data=req_body)
            token_info = response.json()

            session['access_token'] = token_info['access_token']
            session['refresh_token'] = token_info['refresh_token']
            session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

            return redirect('/playlists')

    def get_playlists(self):
        if 'access_token' not in session:
            return redirect('/login')

        if datetime.now().timestamp() > session['expires_at']:
            return redirect('/refresh-token')

        headers = {
            "Authorization": f"Bearer {session['access_token']}"
        }

        # Grab the users playlists
        response = requests.get(self.API_BASE_URL + 'me/playlists', headers=headers)
        playlists = response.json()

        # create a list of track names a duration
        playlist_tracks = []

        for playlist in playlists['items']:
            playlist_id = playlist['id']
            playlist_name = playlist['name']
            
            # Grab tracks for the playlist
            tracks_response = requests.get(self.API_BASE_URL + f'playlists/{playlist_id}/tracks', headers=headers)
            tracks = tracks_response.json()

            # Grab track names and duration
            tracks_info = [
                {
                    'name': track['track']['name'],
                    'duration': f"{track['track']['duration_ms'] // 60000}:{(track['track']['duration_ms'] % 60000) // 1000:02}"
                }
                for track in tracks['items'] if track['track'] and 'duration_ms' in track['track']
            ]

            playlist_tracks.append({
                'playlist_name': playlist_name,
                'tracks': tracks_info
            })

        return render_template('playlists.html', playlists=playlist_tracks)

    def refresh_token(self):
        if 'refresh_token' not in session:
            return redirect('/login')

        if datetime.now().timestamp() > session['expires_at']:
            req_body = {
                'grant_type': 'refresh_token',
                'refresh_token': session['refresh_token'],
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }

            response = requests.post(self.TOKEN_URL, data=req_body)
            new_token_info = response.json()

            session['access_token'] = new_token_info['access_token']
            session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']
            
            return redirect('/playlists')

spotify = Spotify()  # Create an instance of the Spotify class

# Register the routes with Flask
app.route('/')(spotify.index)
app.route('/login')(spotify.login)
app.route('/callback')(spotify.callback)
app.route('/playlists')(spotify.get_playlists)
app.route('/refresh-token')(spotify.refresh_token)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)