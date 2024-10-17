from absl import logging
import json

from util import encryption

_PROD_PARAMS_FILE = "./src/production/params.json.encrypted"
_GCP_PROJECT_ID = "genuine-axle-438304-u4"


class Params():

    def __init__(self, discord_application_id, discord_public_key,
                 discord_client_secret, discord_secret_token):
        self.discord_application_id = discord_application_id
        self.discord_public_key = discord_public_key
        self.discord_client_secret = discord_client_secret
        self.discord_secret_token = discord_secret_token

    @classmethod
    def FromString(cls, plaintext):
        params_dict = json.loads(plaintext)
        return cls(**params_dict)


_PARAMS = None


def GetParams():
    global _PARAMS
    if _PARAMS is not None:
        return _PARAMS

    # Load params.
    with open(_PROD_PARAMS_FILE, "rb") as f:
        ciphertext = f.read()

    location_id = "global"
    key_ring_id = "secrets"
    key_id = "prod_secrets_encryption_key"
    response = encryption.decrypt_symmetric(_GCP_PROJECT_ID, location_id,
                                            key_ring_id, key_id, ciphertext)

    return Params.FromString(response.plaintext)
