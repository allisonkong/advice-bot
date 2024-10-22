from absl import app
from absl import logging
from absl import flags

from advice_bot import AdviceBot
import params


def main(argv):
    secret_token = params.GetParams().discord_params.discord_secret_token
    client = AdviceBot.CreateInstance()
    client.run(secret_token)


if __name__ == "__main__":
    app.run(main)
