from flask import Flask, request, url_for, session, redirect, render_template

import spotipy
from spotipy.oauth2 import SpotifyOAuth

#DEFINING CONSTS
TOKEN_INFO = "token_info"
SHORT_TERM = "short_term"
MEDIUM_TERM = "medium_term"
LONG_TERM = "long_term"
CLIENT_ID = "b3ba4659e52c42c98764656a6c6a17a6"
CLIENT_SECRET = "43f18a3c9d08480887e77feadbc5519c"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=url_for("redirectPage", _external=True),
        scope="user-top-read user-library-read"
    )

app = Flask(__name__)
#this is required for sessions to work
app.secret_key = 'your-secret-key-here'

@app.route("/")
def index():
    name = 'username'
    return render_template('index.html', title='Welcome', username=name)

@app.route("/login")
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirectPage')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code') #redirectPage?code = TOKEN, returns TOKEN
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for("receipt", _external=True))

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        return None
    return token_info

@app.route('/receipt')
def receipt():
    token_info = get_token()
    if not token_info:
        return redirect(url_for('login', _external=True))
    
    try:
        name = 'username'
        sp = spotipy.Spotify(auth=token_info['access_token'])
        # Get recent favorites (last 4 weeks)
        short_term = sp.current_user_top_tracks(
            limit=10,
            offset=0,
            time_range="short_term"
        )

        # Get 6-month favorites (last 6 months)
        medium_term = sp.current_user_top_tracks(
            limit=10,
            offset=0,
            time_range="medium_term"
        )

        # Get all-time favorites
        long_term = sp.current_user_top_tracks(
            limit=10,
            offset=0,
            time_range="long_term"
        )       
        
        return render_template('receipt.html', title='Welcome', username=name, short_term=short_term, medium_term=medium_term, long_term=long_term)
    except Exception as e:
        print(f"Error: {e}")
        # If there's any error with the token, redirect to login
        session.clear()
