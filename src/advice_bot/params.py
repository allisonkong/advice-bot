from absl import logging
from absl import flags
from google.protobuf import text_format
import json
import os.path

from advice_bot.proto import params_pb2
from advice_bot.util import encryption

FLAGS = flags.FLAGS
flags.DEFINE_enum("env", "dev", ["prod", "dev"], "Environment to connect to.")

_PARAMS_CIPHERTEXT = "./production/params.textproto.encrypted"
_PARAMS_PLAINTEXT = "./production/params.textproto"
_GCP_PROJECT_ID = "genuine-axle-438304-u4"

_PARAMS = None


def Params() -> params_pb2.Params:
    """Returns the global singleton params object, initializing it if necessary."""
    global _PARAMS
    if _PARAMS is not None:
        return _PARAMS

    plaintext = ""
    # For ease of development.
    if os.path.exists(_PARAMS_PLAINTEXT):
        with open(_PARAMS_PLAINTEXT, "r") as f:
            plaintext = f.read()
    else:
        with open(_PARAMS_CIPHERTEXT, "rb") as f:
            ciphertext = f.read()

        location_id = "global"
        key_ring_id = "secrets"
        key_id = "prod_secrets_encryption_key"
        response = encryption.decrypt_symmetric(_GCP_PROJECT_ID, location_id,
                                                key_ring_id, key_id, ciphertext)
        plaintext = response.plaintext

    params_map = text_format.Parse(plaintext, params_pb2.ParamsMap())
    if FLAGS.env not in params_map.environments:
        logging.fatal(f"Failed to load params for environment {FLAGS.env}")
    _PARAMS = params_map.environments[FLAGS.env]
    return _PARAMS


def MysqlConnectionArgs() -> dict:
    mysql_params = Params().mysql_params
    args = {}
    args["host"] = mysql_params.host
    args["user"] = mysql_params.user
    args["password"] = mysql_params.password
    args["database"] = mysql_params.database
    args["ssl_ca"] = mysql_params.ssl_ca_file
    args["ssl_cert"] = mysql_params.ssl_cert_file
    args["ssl_key"] = mysql_params.ssl_key_file
    args["ssl_verify_cert"] = True
    return args


_SERVER_CONFIG_MAP = None


def ServerConfigMap() -> dict[int, params_pb2.ServerConfig]:
    global _SERVER_CONFIG_MAP
    if _SERVER_CONFIG_MAP is not None:
        return _SERVER_CONFIG_MAP

    _SERVER_CONFIG_MAP = {}
    for server_config in Params().config.servers:
        _SERVER_CONFIG_MAP[server_config.guild_id] = server_config

    return _SERVER_CONFIG_MAP
