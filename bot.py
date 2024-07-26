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

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

    try:
        guild = bot.get_guild(SERVER_ID)
        if guild is None:
            raise ValueError(f"Guild with ID {SERVER_ID} not found.")

        print(f'Found guild: {guild.name}')
        user = guild.get_member(USER_ID)

        if user is None:
            raise ValueError(f"User with ID {USER_ID} not found in guild.")

        print(f'Found user: {user.name}')
        channel = guild.get_channel(CHANNEL_ID)

        if channel is None:
            raise ValueError(f"Channel with ID {CHANNEL_ID} not found in guild.")

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
        await bot.close()

# Set a timeout to ensure the bot doesn't hang indefinitely
async def timeout_bot():
    await asyncio.sleep(60)
    if not bot.is_closed():
        print('Timeout reached, closing bot')
        await bot.close()

bot.loop.create_task(timeout_bot())
bot.run(TOKEN)
