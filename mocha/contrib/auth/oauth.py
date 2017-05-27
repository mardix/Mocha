"""
Social

"""

import sys
from werkzeug import import_string
from mocha import config, init_app
from flask_oauthlib.client import OAuth

this = sys.modules[__name__]

oauth = OAuth()

_CONFIG = {
    "facebook": {
        'consumer_key': '',
        'consumer_secret': '',
        'scope': '',
        'access_token_method': 'GET',
        'access_token_url': '/oauth/access_token',
        'authorize_url': 'https://www.facebook.com/dialog/oauth',
        'base_url': 'https://graph.facebook.com',
        'request_token_params': {'scope': 'email'},
        'request_token_url': None,
        '__params__': {
            "me": "/me",
            "error_reason": "error_reason",
            "error_description": "error_description"
        }
    },
    "google": {
        'consumer_key': '',
        'consumer_secret': '',
        'access_token_method': 'POST',
        'access_token_url': 'https://accounts.google.com/o/oauth2/token',
        'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
        'base_url': 'https://www.googleapis.com/oauth2/v1/',
        'request_token_params': {'scope': 'email'},
        'request_token_url': None,
        '__params__': {
            "me": "userinfo",
            "error_reason": "error_reason",
            "error_description": "error_description"
        }
    },
    "twitter": {
        'consumer_key': '',
        'consumer_secret': '',
        'access_token_url': 'https://api.twitter.com/oauth/access_token',
        'authorize_url': 'https://api.twitter.com/oauth/authorize',
        'base_url': 'https://api.twitter.com/1.1/',
        'request_token_url': 'https://api.twitter.com/oauth/request_token',
        '__params__': {
            "me": None,
            "user_id": "user_id" # from resp
        }
    },
    "dropbox": {
        'consumer_key': '',
        'consumer_secret': '',
        'access_token_method': 'POST',
        'access_token_url': 'https://api.dropbox.com/1/oauth2/token',
        'authorize_url': 'https://www.dropbox.com/1/oauth2/authorize',
        'base_url': 'https://www.dropbox.com/1/',
        'request_token_params': {},
        'request_token_url': None,
        '__params__': {
            "me": "account/info",
            "error_reason": "error",
            "error_description": "error_description"
        }
    },
    "github": {
        'consumer_key': '',
        'consumer_secret': '',
        'scope': '',
        'access_token_method': 'POST',
        'access_token_url': 'https://github.com/login/oauth/access_token',
        'authorize_url': 'https://github.com/login/oauth/authorize',
        'base_url': 'https://api.github.com/',
        'request_token_params': {'scope': 'user:email'},
        'request_token_url': None,
        '__params__': {
            "me": "user",
            "error_reason": "error",
            "error_description": "error_description"
        }
    },
    "linkedin": {
        'consumer_key': '',
        'consumer_secret': '',
        'access_token_method': 'POST',
        'access_token_url': 'https://www.linkedin.com/uas/oauth2/accessToken',
        'authorize_url': 'https://www.linkedin.com/uas/oauth2/authorization',
        'base_url': 'https://api.linkedin.com/v1/',
        'request_token_params': {'scope': 'basicprofile',
                                 'state': 'RandomString'},
        'request_token_url': None,
        '__params__': {
            "me": "people/~",
            "error_reason": "error",
            "error_description": "error_description"
        }
    }
}


def init_oauth(app):

    oauth.init_app(app)

    oauth_creds = config("OAUTH_CREDENTIALS", {})

    for name, kwargs in oauth_creds.items():
        if "consumer_key" in kwargs and kwargs.get("consumer_key"):
            # swap kwargs, t
            if name in _CONFIG:
                _kwargs = _CONFIG[name]
                _kwargs.update(kwargs)
                kwargs = _kwargs
            params = kwargs.pop("__params__", {})
            provider = oauth.remote_app(name, **kwargs)
            setattr(provider, "__params__", params)
            setattr(this, name, provider)


init_app(init_oauth)
