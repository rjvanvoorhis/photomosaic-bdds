import os


class Environment(object):
    def __init__(self):
        self.default_env = {
            'photomosaic_api_url': 'http://localhost:5000/api/v1/photomosaic',
            'media_bucket': 'images',
            'mongodb_uri': 'mongodb://localhost:27018/',
        }

    def __getattr__(self, item):
        # environment variables overide default configuration
        env_var = {k.lower(): v for k, v in os.environ.items()}.get(item)
        return env_var if env_var is not None else self.default_env.get(item)
