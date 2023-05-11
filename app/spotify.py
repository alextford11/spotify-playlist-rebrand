import base64
import json
import os.path
from logging import getLogger

import requests

from app import get_redis_client
from app.definitions import IMAGES_DIR

SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/'
SPOTIFY_API_URL = 'https://api.spotify.com/v1/'
SPOTIFY_TOKENS_KEY = 'spotify-tokens-key'
AUTH_TOKEN = f'{os.getenv("SPOTIFY_CLIENT_ID")}:{os.getenv("SPOTIFY_CLIENT_SECRET")}'
B64_AUTH_STR = base64.urlsafe_b64encode(AUTH_TOKEN.encode()).decode()
PLAYLISTS = {
    '4iTlYwQTzZ6vm6H0laLFgz': {
        'name': 'SUPER KISSTORY',
        'description': (
            'Old Skool & Anthems. #KISS #KISSFM #KISSTORY #SUPERKISSTORY #OLDSKOOL. Calvin Harris, Kanye West, '
            'Will Smith, Dr. Dre, Eminem, Snoop Dog, Jay-Z, Justin Timberlake, Rihanna, Avicii, David Guetta.'
        ),
        'image': 'kisstory-logo.jpg',
    }
}
redis_cli = get_redis_client()
logger = getLogger(__name__)


class Spotify:
    access_token: str

    def __init__(self):
        tokens = self.get_stored_tokens()
        if tokens:
            self.access_token = tokens['access_token']

    @staticmethod
    def get_stored_tokens():
        tokens_str = redis_cli.get(SPOTIFY_TOKENS_KEY)
        return json.loads(tokens_str) if tokens_str else {}

    def store_tokens(self, tokens):
        self.access_token = tokens['access_token']
        redis_cli.set(SPOTIFY_TOKENS_KEY, json.dumps(tokens))

    def request_and_store_tokens(self, code):
        data = {'grant_type': 'authorization_code', 'code': code, 'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI')}
        headers = {'Authorization': f'Basic {B64_AUTH_STR}', 'Content-Type': 'application/x-www-form-urlencoded'}
        r = requests.post(SPOTIFY_AUTH_URL + 'api/token', data=data, headers=headers)
        assert r.status_code == 200, r.json()

        self.store_tokens(r.json())

    def refresh_and_store_tokens(self):
        tokens = self.get_stored_tokens()
        data = {'grant_type': 'refresh_token', 'refresh_token': tokens['refresh_token']}
        headers = {'Authorization': f'Basic {B64_AUTH_STR}', 'Content-Type': 'application/x-www-form-urlencoded'}
        r = requests.post(SPOTIFY_AUTH_URL + 'api/token', data=data, headers=headers)
        assert r.status_code == 200, r.json()

        tokens.update(r.json())  # refresh token stays the same, but could be new so we just update here
        self.store_tokens(tokens)

    def _request(self, endpoint, method='get', _json=None, data=None, content_type='application/json', count=1):
        url = SPOTIFY_API_URL + endpoint
        _method = getattr(requests, method)
        headers = {'Authorization': 'Bearer ' + self.access_token, 'Content-Type': content_type}
        r = _method(url, json=_json, data=data, headers=headers)
        if count == 1 or r.status_code == 401:
            if count == 5:
                raise RuntimeError(r.status_code, r.json())
            self.refresh_and_store_tokens()
            return self._request(
                endpoint, method=method, _json=_json, data=data, content_type=content_type, count=count + 1
            )
        return r

    def get_playlist(self, playlist_id):
        r = self._request(f'playlists/{playlist_id}?fields=name')
        data = r.json()
        return data

    def update_playlist_details(self, playlist_id, data):
        r = self._request(f'playlists/{playlist_id}', method='put', _json=data)
        assert r.status_code == 200, r.json()

    def update_playlist_image(self, playlist_id, image_name):
        with open(os.path.join(IMAGES_DIR, image_name), 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read())
            r = self._request(
                f'playlists/{playlist_id}/images',
                method='put',
                content_type='image/jpeg',
                data=encoded_string,
            )
        assert r.status_code in [200, 202], r.json()


def is_playlist_name_correct(playlist_id):
    playlist_details = PLAYLISTS[playlist_id]
    sp = Spotify()
    data = sp.get_playlist(playlist_id)
    return data.get('name') == playlist_details['name']


def was_recently_updated():
    return bool(redis_cli.get('SCHEDULER_RECENTLY_RUN'))


def update_playlist_details(playlist_id):
    playlist_details = PLAYLISTS[playlist_id]
    sp = Spotify()
    sp.update_playlist_details(playlist_id, {k: v for k, v in playlist_details.items() if k in ('name', 'description')})
    sp.update_playlist_image(playlist_id, playlist_details['image'])


def scheduler_check_and_execute():
    logger.info('Running scheduler_check_and_execute...')
    for playlist_id in PLAYLISTS:
        is_name_correct = is_playlist_name_correct(playlist_id)
        recently_updated = was_recently_updated()
        logger.info(
            'Checking playlist: %s, details: %s, recently updated: %s', playlist_id, is_name_correct, recently_updated
        )
        if not is_name_correct or not recently_updated:
            logger.info('Updating playlist: %s', playlist_id)
            update_playlist_details(playlist_id)
            redis_cli.set('SCHEDULER_RECENTLY_RUN', 1, 3600 * 12)
