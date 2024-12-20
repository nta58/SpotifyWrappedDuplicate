from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import uuid

#DEFINING CONSTS
TOKEN_INFO = "token_info"
SHORT_TERM = "short_term"
MEDIUM_TERM = "medium_term"
LONG_TERM = "long_term"
CLIENT_ID = "b3ba4659e52c42c98764656a6c6a17a6"
CLIENT_SECRET = "43f18a3c9d08480887e77feadbc5519c"

def create_spotify_oauth(user_session=None):
    cache_path = None if user_session is None else f".cache-{user_session}"
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=url_for("redirectPage", _external=True),
        scope="user-top-read user-library-read",
        cache_path=cache_path
    )

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

@app.route("/")
def index():
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())
    return render_template('index.html', title='Welcome')

@app.route("/login")
def login():
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())
    sp_oauth = create_spotify_oauth(session.get('uuid'))
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirectPage')
def redirectPage():
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())
    sp_oauth = create_spotify_oauth(session.get('uuid'))
    code = request.args.get('code')
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
        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        # Get user's actual name from Spotify
        user_info = sp.current_user()
        username = user_info['display_name']
        
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
        
        return render_template('receipt.html', 
                             title='Your Spotify Receipt', 
                             username=username,
                             short_term=short_term, 
                             medium_term=medium_term, 
                             long_term=long_term)
    except Exception as e:
        print(f"Error: {e}")
        session.clear()
        return redirect(url_for('login', _external=True))

if __name__ == '__main__':
    app.run(debug=True)