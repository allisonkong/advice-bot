#!/usr/bin/env python3

import discord
import params
from absl import app
from absl import logging
from absl import flags
import gunicorn.app.base

from frontend import server

FLAGS = flags.FLAGS

flags.DEFINE_bool("build", True, "Rebuild js before running server")
flags.DEFINE_integer("gunicorn_workers", 1, "Number of gunicorn workers")
flags.DEFINE_string("bind", "127.0.0.1:9001", "Host and port number")


class ApplicationWrapper(gunicorn.app.base.BaseApplication):
    """Wrapper for gunicorn."""

    def __init__(self, application, config):
        self.application = application
        self.config = config
        super(ApplicationWrapper, self).__init__()

    def load_config(self):
        for key in self.config:
            value = self.config[key]
            if key not in self.cfg.settings or value is None:
                continue
            self.cfg.set(key, value)

    def load(self):
        return self.application


class AdviceBot(discord.Client):

    async def on_ready(self) -> None:
        print("Logged on as {}".format(self.user))

    async def on_message(self, message: discord.Message) -> None:
        print("---Message received---")
        print("Author: {}".format(message.author.name))
        print("Author ID: {}".format(message.id))
        print("Author global name: {}".format(message.author.global_name))
        print("Author display name: {}".format(message.author.display_name))
        print("Content: {}".format(message.content))
        print("Channel: {}".format(message.channel.name))
        print("Channel ID: {}".format(message.channel.id))
        print("Guild: {}".format(message.channel.guild.name))
        print("Guild ID: {}".format(message.channel.guild.id))
        print("Guild Owner: {}".format(message.channel.guild.owner))
        for channel in message.channel.guild.channels:
            print("Channel: {}".format(channel.name))
            print("Channel ID: {}".format(channel.id))


def run_advice_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    client = AdviceBot(
        application_id=params.GetParams().discord_params.discord_application_id,
        intents=intents)
    client.run(params.GetParams().discord_params.discord_secret_token)


def main(argv):
    gunicorn_config = {
        "accesslog": "-",
        "bind": FLAGS.bind,
        "workers": FLAGS.gunicorn_workers,
    }

    ApplicationWrapper(server.NewInstance(), gunicorn_config).run()


if __name__ == "__main__":
    app.run(main)
