import base64
import json
import os.path
from json import JSONDecodeError

import requests

from app.definitions import ROOT_DIR, IMAGES_DIR

SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/'
SPOTIFY_API_URL = 'https://api.spotify.com/v1/'
SPOTIFY_ACCESS_TOKEN_JSON = os.path.join(ROOT_DIR, 'spotify-tokens.json')
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


class Spotify:
    access_token: str

    def __init__(self):
        tokens = self.get_stored_tokens()
        print(tokens)
        if tokens:
            self.access_token = tokens['access_token']

    @staticmethod
    def get_stored_tokens():
        print(SPOTIFY_ACCESS_TOKEN_JSON)
        print([f for f in os.listdir(ROOT_DIR)])
        with open(SPOTIFY_ACCESS_TOKEN_JSON, 'r+') as f:
            tokens = json.load(f)
            print(tokens)

        try:
            with open(SPOTIFY_ACCESS_TOKEN_JSON, 'r+') as f:
                tokens = json.load(f)
        except (FileNotFoundError, JSONDecodeError) as e:
            print(e)
            tokens = {}
        return tokens

    def store_tokens(self, tokens):
        self.access_token = tokens['access_token']
        with open(SPOTIFY_ACCESS_TOKEN_JSON, 'w+') as f:
            json.dump(tokens, f)

    def request_and_store_tokens(self, code):
        data = {'grant_type': 'authorization_code', 'code': code, 'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI')}
        auth_token = f'{os.getenv("SPOTIFY_CLIENT_ID")}:{os.getenv("SPOTIFY_CLIENT_SECRET")}'
        b64_auth_str = base64.urlsafe_b64encode(auth_token.encode()).decode()
        headers = {'Authorization': f'Basic {b64_auth_str}', 'Content-Type': 'application/x-www-form-urlencoded'}
        r = requests.post(SPOTIFY_AUTH_URL + 'api/token', data=data, headers=headers)
        assert r.status_code == 200, r.json()

        self.store_tokens(r.json())

    def refresh_tokens(self):
        tokens = self.get_stored_tokens()
        refresh_token = tokens['refresh_token']
        self.request_and_store_tokens(refresh_token)

    def _request(self, endpoint, method='get', _json=None, data=None, content_type='application/json', count=1):
        url = SPOTIFY_API_URL + endpoint
        method = getattr(requests, method)
        headers = {'Authorization': 'Bearer ' + self.access_token, 'Content-Type': content_type}
        r = method(url, json=_json, data=data, headers=headers)
        if r.status_code == 401:
            if count == 5:
                raise RuntimeError(r.status_code, r.json())
            self.refresh_tokens()
            return self._request(endpoint, method, data, content_type, count=count + 1)
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


def check_playlist_name_correct(playlist_id):
    playlist_details = PLAYLISTS[playlist_id]
    sp = Spotify()
    data = sp.get_playlist(playlist_id)
    return data.get('name') == playlist_details['name']


def update_playlist_details(playlist_id):
    playlist_details = PLAYLISTS[playlist_id]
    sp = Spotify()
    sp.update_playlist_details(playlist_id, {k: v for k, v in playlist_details.items() if k in ('name', 'description')})
    sp.update_playlist_image(playlist_id, playlist_details['image'])
    return


def scheduler_check_and_execute():
    for playlist_id in PLAYLISTS:
        if not check_playlist_name_correct(playlist_id):
            update_playlist_details(playlist_id)
