#!/usr/bin/env python3

import discord
from params import GetParams


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


def main():
    intents = discord.Intents.default()
    intents.message_content = True
    client = AdviceBot(application_id=GetParams().discord_application_id,
                       intents=intents)
    client.run(GetParams().discord_secret_token)


if __name__ == "__main__":
    main()
