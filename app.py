from flask import Flask, request, url_for, session, redirect, render_template, flash
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# DEFINING CONSTS
TOKEN_INFO = "token_info"
SHORT_TERM = "short_term"
MEDIUM_TERM = "medium_term"
LONG_TERM = "long_term"

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

def get_token():
    try:
        token_info = session.get(TOKEN_INFO, None)
        if not token_info:
            return None

        # Check if token has expired
        now = int(time.time())
        is_expired = token_info['expires_at'] - now < 60
        if is_expired:
            spotify_oauth = create_spotify_oauth()
            token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
            session[TOKEN_INFO] = token_info

        return token_info
    except Exception as e:
        app.logger.error(f"Error getting token: {e}")
        return None

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.environ.get('SPOTIFY_CLIENT_ID'),
        client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=url_for("redirectPage", _external=True),
        scope="user-top-read user-library-read",
        show_dialog=True,
        cache_handler=None
    )
        
def clear_session_cache():
    try:
        if 'uuid' in session:
            cache_path = f".cache-{session['uuid']}"
            if os.path.exists(cache_path):
                os.remove(cache_path)
        session.clear()
    except Exception as e:
        app.logger.error(f"Error clearing session cache: {e}")

@app.route("/")
def index():
    clear_session_cache()
    session['uuid'] = str(uuid.uuid4())
    return render_template('index.html', title='Welcome to Spotify Wrapped Duplicate')

@app.route("/login")
def login():
    try:
        clear_session_cache()
        session['uuid'] = str(uuid.uuid4())
        spotify_oauth = create_spotify_oauth()
        auth_url = spotify_oauth.get_authorize_url()
        return redirect(auth_url)
    except Exception as e:
        app.logger.error(f"Login error: {e}")
        flash('An error occurred during login. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/redirectPage')
def redirectPage():
    try:
        code = request.args.get('code')
        if not code:
            flash('Authorization failed. Please try again.', 'error')
            return redirect(url_for('login'))
            
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.get_access_token(code)
        session[TOKEN_INFO] = token_info
        session['uuid'] = str(uuid.uuid4())
        return redirect(url_for("receipt"))
    except Exception as e:
        app.logger.error(f"Redirect error: {e}")
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route('/receipt')
def receipt():
    if 'uuid' not in session:
        return redirect(url_for('login'))
    
    token_info = get_token()
    if not token_info:
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('login'))
        
    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        current_user = sp.current_user()
        
        top_tracks = {}
        time_ranges = {
            'short_term': 'Last 4 Weeks',
            'medium_term': 'Last 6 Months',
            'long_term': 'All Time'
        }

        for time_range in time_ranges.keys():
            top_tracks[time_range] = sp.current_user_top_tracks(
                limit=10,
                offset=0,
                time_range=time_range
            )
        
        return render_template('receipt.html', 
                             title='Your Spotify Stats',
                             username=current_user['display_name'],
                             short_term=top_tracks['short_term'],
                             medium_term=top_tracks['medium_term'],
                             long_term=top_tracks['long_term'])
    except Exception as e:
        app.logger.error(f"Error in receipt route: {e}")
        flash('Failed to fetch your Spotify data. Please try again.', 'error')
        clear_session_cache()
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    clear_session_cache()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=False)  # Set to False in production