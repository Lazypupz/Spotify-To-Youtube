from dotenv import load_dotenv
import os
from flask import Flask, redirect, request, jsonify, session, render_template
from app import Spotify

load_dotenv()

API_KEY = os.getenv("YOUTUBEAPI")
client_secret = os.getenv("YOUTUBE_OAUTH")
REDIRECT_URI = "http://localhost:5000/callback" 

def grabSpot(): 
    pass

class Youtube:
    def __init__(self):
        pass
        #test
        #test