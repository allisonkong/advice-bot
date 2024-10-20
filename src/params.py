from absl import logging
import json
import os.path

from util import encryption

_PROD_PARAMS_CIPHERTEXT = "./src/production/params.json.encrypted"
_PROD_PARAMS_PLAINTEXT = "./src/production/params.json"
_GCP_PROJECT_ID = "genuine-axle-438304-u4"


class Params():

    def __init__(self, discord_params: dict, frontend_params: dict,
                 database_params: dict):
        self.discord_params = DiscordParams(**discord_params)
        self.frontend_params = FrontendParams(**frontend_params)
        self.database_params = DatabaseParams(**database_params)

    @classmethod
    def FromString(cls, plaintext: str):
        params_dict = json.loads(plaintext)
        return cls(**params_dict)


class DiscordParams():

    def __init__(self, discord_application_id: str, discord_public_key: str,
                 discord_client_secret: str, discord_secret_token: str):
        self.discord_application_id = discord_application_id
        self.discord_public_key = discord_public_key
        self.discord_client_secret = discord_client_secret
        self.discord_secret_token = discord_secret_token


class FrontendParams():

    def __init__(self, secret_key: str):
        self.MAX_CONTENT_LENGTH = 1 * 1024 * 1024 * 1024
        self.SECRET_KEY = secret_key
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = "Lax"


class DatabaseParams():

    def __init__(self):
        pass


_PARAMS = None


def GetParams() -> Params:
    """Returns the global singleton params object, initializing it if necessary."""
    global _PARAMS
    if _PARAMS is not None:
        return _PARAMS

    plaintext = ""
    if os.path.exists(_PROD_PARAMS_PLAINTEXT):
        with open(_PROD_PARAMS_PLAINTEXT, "r") as f:
            plaintext = f.read()
    else:
        with open(_PROD_PARAMS_CIPHERTEXT, "rb") as f:
            ciphertext = f.read()

        location_id = "global"
        key_ring_id = "secrets"
        key_id = "prod_secrets_encryption_key"
        response = encryption.decrypt_symmetric(_GCP_PROJECT_ID, location_id,
                                                key_ring_id, key_id, ciphertext)
        plaintext = response.plaintext

    return Params.FromString(plaintext)
