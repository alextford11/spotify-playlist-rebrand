import os

from flask import Blueprint, redirect, render_template, request

from app.spotify import SPOTIFY_AUTH_URL, Spotify

index_blueprint = Blueprint('index', __name__)


@index_blueprint.route('/')
def spotify_login():
    """View to show spotify login for OAuth"""
    spotify_url = SPOTIFY_AUTH_URL + 'authorize'
    spotify_url += '?response_type=code'
    spotify_url += '&client_id=' + os.getenv('SPOTIFY_CLIENT_ID')
    spotify_url += '&scope=' + os.getenv('SPOTIFY_SCOPE')
    spotify_url += '&redirect_uri=' + os.getenv('SPOTIFY_REDIRECT_URI')
    spotify_url += '&state=' + os.getenv('SPOTIFY_STATE')
    return redirect(spotify_url)


@index_blueprint.route('/callback/')
def callback():
    assert request.args.get('state') == os.getenv('SPOTIFY_STATE')

    sp = Spotify()
    sp.request_and_store_tokens(request.args['code'])
    return render_template('index.html')
