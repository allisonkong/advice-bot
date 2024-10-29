from absl import app
from absl import flags
from absl import logging
import discord
import os
import pathlib

from advice_bot.advice_bot import AdviceBot
from advice_bot import params


def SetupLogging():
    log_dir = os.path.expanduser("~/.logs/")
    # Make dir if necessary.
    os.makedirs(log_dir, mode=0o700, exist_ok=True)

    absl_handler = logging.get_absl_handler()
    absl_handler.use_absl_log_file(program_name="advice_bot.py",
                                   log_dir=log_dir)
    logging.use_absl_handler()


def main(argv):
    SetupLogging()
    secret_token = params.Params().discord_params.discord_secret_token
    client = AdviceBot.CreateInstance()
    client.run(secret_token)


if __name__ == "__main__":
    app.run(main)
