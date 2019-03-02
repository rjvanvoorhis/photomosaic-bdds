import os
import socket
from copy import deepcopy
import functools


def singleton(cls):
    """Make a class a Singleton class (only one instance)"""
    @functools.wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        if not wrapper_singleton.instance:
            wrapper_singleton.instance = cls(*args, **kwargs)
        return wrapper_singleton.instance
    wrapper_singleton.instance = None
    return wrapper_singleton


def get_broadcast_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    broad_cast_ip = (s.getsockname()[0])
    s.close()
    return broad_cast_ip


@singleton
class Environment(object):
    def __init__(self):
        broadcast_ip = get_broadcast_ip()
        self.persistent_fields = [
            'mail_username',
            'mail_password',
            'behave_password'
        ]
        self.fields = [
            'broadcast_ip',
            's3_port',
            'mongodb_port',
            'mosaic_api_port',
            'mosaic_api_host',
            'mock_mosaic_external_port',
            'mock_mosaic_internal_port',
            'photomosaic_port',
            'photomosaic_domain',
            's3_endpoint_url',
            's3_external_url',
            'mosaic_api_url_internal',
            'mosaic_api_url_external',
            'mail_username',
            'mail_password',
            's3_data_directory',
            'mongodb_data_directory',
            'admin_username',
            'admin_email',
            'user_username',
            'user_email',
            'behave_password',
            'mosaic_api_url'
        ]
        self.environ = {
            'local': {
                'broadcast_ip': broadcast_ip,
                's3_port': 81,
                'mongodb_port': 27019,
                'mosaic_api_port': 5001,
                'mosaic_api_host': broadcast_ip,
                'mock_mosaic_external_port': 5081,
                'mock_mosaic_internal_port': 5080,
                'photomosaic_port': 5080,
                'photomosaic_domain': 'mock-mosaic-maker',
                's3_endpoint_url': 'http://local-s3:80/',
                's3_external_url': f'http://{broadcast_ip}:81',
                'mosaic_api_url_internal': 'http://mosaic-api:5000/api/v1/photomosaic',
                'mosaic_api_url_external': f'http://{broadcast_ip}:5001/api/v1/photomosaic',
                'mail_username': '',
                'mail_password': '',
                's3_data_directory': os.path.abspath('s3_volume'),
                'mongodb_data_directory': os.path.abspath('mongodb_volume'),
                'admin_username': 'behave_admin_user',
                'admin_email': 'photomosaic.api.admin@gmail.com',
                'user_username': 'behave_basic_user',
                'user_email': 'photomosaic.api.user@gmail.com',
                'behave_password': ''
            },
            'docker_compose': {
                'broadcast_ip': broadcast_ip,
                's3_port': 81,
                'mongodb_port': 27017,
                'mosaic_api_port': 5000,
                'mosaic_api_host': 'mosaic-api',
                'mock_mosaic_external_port': 5081,
                'mock_mosaic_internal_port': 5080,
                'photomosaic_port': 5080,
                'photomosaic_domain': 'mock-mosaic-maker',
                's3_endpoint_url': 'http://local-s3:80/',
                's3_external_url': f'http://{broadcast_ip}:81',
                'mosaic_api_url_internal': 'http://mosaic-api:5000/api/v1/photomosaic',
                'mosaic_api_url_external': f'http://{broadcast_ip}:5081/api/v1/photomosaic',
                'mail_username': '',
                'mail_password': '',
                's3_data_directory': os.path.abspath('s3_volume'),
                'mongodb_data_directory': os.path.abspath('mongodb_volume'),
                'admin_username': 'behave_admin_user',
                'admin_email': 'photomosaic.api.admin@gmail.com',
                'user_username': 'behave_basic_user',
                'user_email': 'photomosaic.api.user@gmail.com',
                'behave_password': ''
            },
           'swarm': {
                'broadcast_ip': broadcast_ip,
                's3_port': 81,
                'mongodb_port': 27017,
                'mosaic_api_port': 5000,
                'mosaic_api_host': 'mosaic-api',
                'mock_mosaic_external_port': 5081,
                'mock_mosaic_internal_port': 5080,
                'photomosaic_port': 8080,
                'photomosaic_domain': 'faas-swarm',
                's3_endpoint_url': 'http://local-s3:80/',
                's3_external_url': f'http://{broadcast_ip}:81',
                'mosaic_api_url_internal': 'http://mosaic-api:5000/api/v1/photomosaic',
                'mosaic_api_url_external': f'http://{broadcast_ip}:5000/api/v1/photomosaic',
                'mail_username': '',
                'mail_password': '',
                's3_data_directory': os.path.abspath('s3_volume'),
                'mongodb_data_directory': os.path.abspath('mongodb_volume'),
                'admin_username': 'behave_admin_user',
                'admin_email': 'photomosaic.api.admin@gmail.com',
                'user_username': 'behave_basic_user',
                'user_email': 'photomosaic.api.user@gmail.com',
                'behave_password': '',
            }
        }

    def __getattr__(self, key):
        environ = deepcopy(self.environ.get(os.environ.get('ENVIRONMENT', 'local'), {}))
        environ.update({k.lower().replace('-', '_'): v for k, v in os.environ.items()})
        mosaic_api_url = f'http://{environ.get("mosaic_api_host")}:{environ.get("mosaic_api_port")}/api/v1/photomosaic'
        environ['mosaic_api_url'] = mosaic_api_url
        return environ.get(key.lower())

    def export_environments(self):
        with open('.env', 'w+') as fn:
            fn.write('\n'.join(f'{key.upper()}={self.__getattr__(key)}' for key in self.fields))
        with open('postactivate.sh', 'w+') as fn:
            fn.write('\n'.join(f'export {key.upper()}="{self.__getattr__(key)}"' for key in self.fields))
        with open('postdeactivate.sh', 'w+') as fn:
            fn.write('\n'.join(f'unset {field.upper()}' for field in self.fields
                               if field not in self.persistent_fields))

