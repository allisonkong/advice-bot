from absl import app
from absl import flags
import discord
import logging as py_logging
import logging.handlers as handlers
import os
import pathlib

from advice_bot.advice_bot import AdviceBot
from advice_bot import params


def SetupLogging():
    log_filename = os.path.expanduser("~/.logs/advice_bot.log")
    log_dir = os.path.dirname(log_filename)
    # Make dir if necessary.
    os.makedirs(log_dir, mode=0o700, exist_ok=True)
    handler = handlers.TimedRotatingFileHandler(log_filename,
                                                when="midnight",
                                                interval=1,
                                                backupCount=180,
                                                utc=True)

    logger = py_logging.getLogger("absl")
    logger.setLevel(py_logging.INFO)
    logger.addHandler(handler)

    logger = py_logging.getLogger("discord")
    logger.setLevel(py_logging.INFO)
    logger.addHandler(handler)


def main(argv):
    SetupLogging()
    secret_token = params.Params().discord_params.discord_secret_token
    client = AdviceBot.CreateInstance()
    client.run(secret_token)


if __name__ == "__main__":
    app.run(main)
