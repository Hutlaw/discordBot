# bot.py

import discord
import os
import aiohttp
import asyncio

# Retrieve the bot token from environment variables (GitHub secrets)
TOKEN = os.getenv('DToken')

# Define the server and channel IDs
SERVER_ID = 1143308869817356428
CHANNEL_ID = 1266202982182162482
USER_ID = 849456491131043840

# Create an instance of the bot with necessary intents
intents = discord.Intents.default()
intents.members = True  # Enable the members intent

class DiscordBot(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f'Logged in as {self.user.name}')
        try:
            guild = self.get_guild(SERVER_ID)
            if guild is None:
                print(f"Error: Guild with ID {SERVER_ID} not found.")
                return

            print(f'Found guild: {guild.name}')
            user = guild.get_member(USER_ID)

            if user is None:
                print(f"Error: User with ID {USER_ID} not found in guild.")
                return

            print(f'Found user: {user.name}')
            channel = guild.get_channel(CHANNEL_ID)

            if channel is None:
                print(f"Error: Channel with ID {CHANNEL_ID} not found in guild.")
                return

            print(f'Found channel: {channel.name}')
            
            # Get user's profile picture URL
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            print(f'User avatar URL: {avatar_url}')
            
            # Download the profile picture
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as response:
                    if response.status == 200:
                        file_path = 'profile_picture.png'
                        with open(file_path, 'wb') as f:
                            f.write(await response.read())
                        
                        print('Profile picture downloaded')
                        
                        # Send the profile picture to the channel and ping the user
                        await channel.send(content=f'<@{USER_ID}>', file=discord.File(file_path))
                        print('Profile picture sent to channel')

                        # Clean up the file after sending
                        os.remove(file_path)
                    else:
                        await channel.send(
                            content=f'<@{USER_ID}>',
                            embed=discord.Embed(description="Failed to retrieve profile picture.")
                        )
                        print('Failed to retrieve profile picture')

        except Exception as e:
            print(f'Error: {e}')

        finally:
            await self.close()

    async def setup_hook(self):
        # Run any asynchronous initialization here
        self.bg_task = self.loop.create_task(self.timeout_bot())

    async def timeout_bot(self):
        await asyncio.sleep(60)
        if not self.is_closed():
            print('Timeout reached, closing bot')
            await self.close()

async def main():
    bot = DiscordBot(intents=intents)
    await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
