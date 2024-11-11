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
import yt




def main():

    github_url = "https://github.com/Lazypupz"

    print(f"Welcome to Spotify-to-Youtube app from Lazypupz  - {github_url} \n")
    print("Please make sure you have your own personal API keys and authentication set up in the README on Github (*required*).\n")

    spotify = sp.Spotify()
    spotify.login()
    playlists = spotify.get_playlists()


    youtube_api = yt.YoutubeAPI()
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
            youtube_api = yt.YoutubeAPI()
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

#test