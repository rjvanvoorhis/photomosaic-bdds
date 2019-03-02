__all__ = ['PhotomosaicAccessor']

import requests
from features.steps.environment import Environment


class PhotomosaicAccessor(object):
    def __init__(self):
        self.base_url = f'{Environment().mosaic_api_url_external}'

    def get(self, endpoint, **kwargs):
        url = f'{self.base_url}{endpoint}'
        return requests.get(url, **kwargs)

    def put(self, endpoint, **kwargs):
        url = f'{self.base_url}{endpoint}'
        return requests.put(url, **kwargs)

    def post(self, endpoint, **kwargs):
        url = f'{self.base_url}{endpoint}'
        return requests.post(url, **kwargs)

    def patch(self, endpoint, **kwargs):
        url = f'{self.base_url}{endpoint}'
        return requests.patch(url, **kwargs)

    def delete(self, endpoint, **kwargs):
        url = f'{self.base_url}{endpoint}'
        return requests.delete(url, **kwargs)

    def get_auth_header(self, role):
        password = Environment().behave_password
        username = Environment().__getattr__(f'{role.lower()}_username')
        return self.login(username=username, password=password).json()

    def delete_user(self, username, headers=None):
        headers = {} if not headers else headers
        return self.delete(f'/users/{username}', headers=headers)

    def register(self, username=None, email=None, password=None):
        user_info = {
            'username': username if username else Environment().behave_username,
            'password': password if password else Environment().behave_password,
            'email': email if email else Environment().behave_email,
        }
        return self.post('/register', json=user_info)

    def validate(self, username=None, password=None):
        user_info = {
            'username': username if username else Environment().behave_username,
            'password': password if password else Environment().behave_password,
        }
        return self.post('/validate', json=user_info)

    def login(self, username=None, password=None):
        user_info = {
            'username': username if username else Environment().behave_username,
            'password': password if password else Environment().behave_password,
        }
        return self.post('/login', json=user_info)

    def create_user(self, username=None, password=None, email=None, auth=None):
        auth = auth if auth else self.get_auth_header('admin')
        resp = self.delete_user(username=username, headers=auth)
        print(resp.text)
        resp = self.register(username=username, password=password, email=email)
        print(resp.text)
        return self.validate(username=username, password=password)

    def upload_file(self, username, fp, headers=None):
        headers = headers if headers else {}
        url = f'/users/{username}/uploads'
        print(url)
        print(fp)
        with open(fp, 'rb') as fn:
            resp = self.post(url, files={'file': fn}, headers=headers)
        return resp

    def send_message(self, username, file_id, enlargement, tile_size, headers=None):
        headers = headers if headers else {}
        message_info = {
            'file_id': file_id,
            'enlargement': enlargement,
            'tile_size': tile_size
        }
        return self.post(f'/users/{username}/messages', json=message_info, headers=headers)

    def get_pending(self, username, as_json=True, headers=None):
        headers = headers if headers else {}
        url = f'/users/{username}/pending{"_json" if as_json else ""}'
        return self.get(url, headers=headers)

    def get_image(self, file_id):
        return self.get(f'/images/{file_id}')

    def get_gallery(self, username, query=None, headers=None):
        headers = headers if headers else {}
        query = query if query else ''
        return self.get(f'/users/{username}/gallery{query}', headers=headers)
