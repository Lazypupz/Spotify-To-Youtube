from flask import Flask, redirect, request, jsonify, session, render_template
import requests
from dotenv import load_dotenv
import os
import urllib.parse
from datetime import datetime

load_dotenv()
#recieves keys fron .env file
client_id = os.getenv('SPOTIFYCLIENT_ID')
client_secret = os.getenv('SPOTIFYCLIENT_SECRET')

app = Flask(__name__)
app.secret_key = os.getenv("flask_key")


REDIRECT_URI = 'http://localhost:5000/callback'

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    scope = "user-read-private user-read-email playlist-read-private playlist-read-collaborative"

    params = {
        'client_id': client_id,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)



@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({'error': request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/playlists')

@app.route('/playlists')
def get_playlists():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        "Authorization": f"Bearer {session['access_token']}"
    }

    # Fetch the user's playlists
    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists = response.json()
    
    # Prepare a list to hold playlists and their tracks
    playlist_tracks = []

    for playlist in playlists['items']:
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        
        # Fetch tracks for the playlist
        tracks_response = requests.get(API_BASE_URL + f'playlists/{playlist_id}/tracks', headers=headers)
        tracks = tracks_response.json()

        # Extract track names
        track_names = [track['track']['name'] for track in tracks['items'] if track['track']]
        track_dur = [track['duration_ms']for track in tracks['items'] if track['track']]

        playlist_tracks.append({
            'playlist_name': playlist_name,
            'tracks': track_names & track_dur
        })

    
    return render_template('playlists.html', playlists=playlist_tracks)

#refresh token every hour
@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': client_id,
            'client_secret': client_secret
        }
    
        response = requests.post(TOKEN_URL, data = req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']
        

        return redirect('/playlists')

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)