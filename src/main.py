#!/usr/bin/env python3

import discord
import params


class AdviceBot(discord.Client):

    async def on_ready(self):
        print("Logged on as {}".format(self.user))

    async def on_message(self, message):
        print("{}: {}".format(message.author, message.content))


def main():
    intents = discord.Intents.default()
    intents.message_content = True
    client = AdviceBot(intents=intents)
    client.run(params.GetParams().discord_secret_token)


if __name__ == "__main__":
    main()
