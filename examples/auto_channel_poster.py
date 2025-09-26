"""Auto poster and DM responder using discord.py-self.

Usage:
    export DISCORD_TOKEN=...  # Your user token
    export TARGET_CHANNEL_ID=123456789012345678
    export SCHEDULED_MESSAGE="Hello, world!"
    export DM_RESPONSE="Here is my Discord server: https://discord.gg/..."
    python examples/auto_channel_poster.py
"""
import os
from typing import Optional

import discord
from discord.ext import tasks

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID_ENV = os.getenv("TARGET_CHANNEL_ID")
SCHEDULED_MESSAGE = os.getenv("SCHEDULED_MESSAGE", "Hello from discord.py-self!")
DM_RESPONSE = os.getenv(
    "DM_RESPONSE",
    "Here is my Discord server invite: https://discord.gg/your-server",
)

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable is required")

if CHANNEL_ID_ENV is None:
    raise RuntimeError("TARGET_CHANNEL_ID environment variable is required")

try:
    TARGET_CHANNEL_ID = int(CHANNEL_ID_ENV)
except ValueError as exc:
    raise RuntimeError("TARGET_CHANNEL_ID must be an integer") from exc


def _create_client() -> discord.Client:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.dm_messages = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        print(f"Logged in as {client.user} ({client.user.id})")
        if not post_scheduled_message.is_running():
            post_scheduled_message.start()

        channel = await get_target_channel(client)
        if channel is not None:
            await channel.send(SCHEDULED_MESSAGE)
            print("Posted initial message")
        else:
            print(f"Unable to find channel with ID {TARGET_CHANNEL_ID}")

    @client.event
    async def on_message(message: discord.Message) -> None:
        if message.author.id == client.user.id:
            return

        if isinstance(message.channel, discord.DMChannel):
            await respond_to_dm(message)

    @tasks.loop(hours=2)
    async def post_scheduled_message() -> None:
        channel = await get_target_channel(client)
        if channel is None:
            print(f"Unable to find channel with ID {TARGET_CHANNEL_ID}")
            return

        await channel.send(SCHEDULED_MESSAGE)
        print("Posted scheduled message")

    @post_scheduled_message.before_loop
    async def before_post_scheduled_message() -> None:
        await client.wait_until_ready()

    async def respond_to_dm(message: discord.Message) -> None:
        try:
            await message.channel.send(DM_RESPONSE)
            print(f"Responded to DM from {message.author}")
        except discord.HTTPException as error:
            print(f"Failed to respond to DM: {error}")

    async def get_target_channel(client: discord.Client) -> Optional[discord.abc.MessageableChannel]:
        channel = client.get_channel(TARGET_CHANNEL_ID)
        if channel is not None:
            return channel

        try:
            return await client.fetch_channel(TARGET_CHANNEL_ID)
        except discord.HTTPException as error:
            print(f"Failed to fetch channel: {error}")
            return None

    return client


def main() -> None:
    client = _create_client()
    client.run(TOKEN)


if __name__ == "__main__":
    main()
