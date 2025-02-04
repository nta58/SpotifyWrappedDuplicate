from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import uuid
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#DEFINING CONSTS
TOKEN_INFO = "token_info"
SHORT_TERM = "short_term"
MEDIUM_TERM = "medium_term"
LONG_TERM = "long_term"
CLIENT_ID = "b3ba4659e52c42c98764656a6c6a17a6"
CLIENT_SECRET = "43f18a3c9d08480887e77feadbc5519c"

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

@app.route("/")
def index():
    logger.debug("Accessing index route")
    try:
        clear_session_cache()
        session['uuid'] = str(uuid.uuid4())
        logger.debug("Session UUID set")
        return render_template('index.html', title='Welcome')
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return str(e), 500

def get_token():
    logger.debug("Getting token")
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        return None

    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
        session[TOKEN_INFO] = token_info

    return token_info

def create_spotify_oauth():
    logger.debug("Creating Spotify OAuth")
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=url_for("redirectPage", _external=True),
        scope="user-top-read user-library-read",
        show_dialog=True,
        cache_handler=None
    )
        
def clear_session_cache():
    logger.debug("Clearing session cache")
    if 'uuid' in session:
        cache_path = f".cache-{session['uuid']}"
        if os.path.exists(cache_path):
            os.remove(cache_path)
    session.clear()

@app.route("/login")
def login():
    logger.debug("Accessing login route")
    try:
        clear_session_cache()
        session['uuid'] = str(uuid.uuid4())
        spotify_oauth = create_spotify_oauth()
        auth_url = spotify_oauth.get_authorize_url()
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        return str(e), 500

@app.route('/redirectPage')
def redirectPage():
    logger.debug("Accessing redirect route")
    try:
        code = request.args.get('code')
        if not code:
            return redirect(url_for('login'))
            
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.get_access_token(code)
        session[TOKEN_INFO] = token_info
        session['uuid'] = str(uuid.uuid4())
        return redirect(url_for("receipt"))
    except Exception as e:
        logger.error(f"Error in redirect route: {str(e)}")
        return str(e), 500

@app.route('/receipt')
def receipt():
    logger.debug("Accessing receipt route")
    try:
        if 'uuid' not in session:
            return redirect(url_for('login'))
        
        token_info = get_token()
        if not token_info:
            return redirect(url_for('login'))
            
        sp = spotipy.Spotify(auth=token_info['access_token'])
        current_user = sp.current_user()
        
        short_term = sp.current_user_top_tracks(
            limit=10,
            offset=0,
            time_range="short_term"
        )

        medium_term = sp.current_user_top_tracks(
            limit=10,
            offset=0,
            time_range="medium_term"
        )

        long_term = sp.current_user_top_tracks(
            limit=10,
            offset=0,
            time_range="long_term"
        )       
        
        return render_template('receipt.html', 
                             title='Your Spotify Receipt', 
                             username=current_user['display_name'],
                             short_term=short_term, 
                             medium_term=medium_term, 
                             long_term=long_term)
    except Exception as e:
        logger.error(f"Error in receipt route: {str(e)}")
        return str(e), 500

@app.route('/logout')
def logout():
    logger.debug("Accessing logout route")
    try:
        clear_session_cache()
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in logout route: {str(e)}")
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)