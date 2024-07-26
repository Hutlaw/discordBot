import discord
import os

# Retrieve the bot token from environment variables (GitHub secrets)
TOKEN = os.getenv('DToken')

# Define the server and channel IDs
SERVER_ID = 1143308869817356428
CHANNEL_ID = 1266202982182162482
USER_ID = 849456491131043840

# Create an instance of the bot
intents = discord.Intents.default()
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    guild = bot.get_guild(SERVER_ID)
    if guild:
        user = guild.get_member(USER_ID)
        if user:
            channel = guild.get_channel(CHANNEL_ID)
            if channel:
                # Get user's profile picture URL
                avatar_url = user.avatar.url
                # Download the profile picture
                async with bot.http._session.get(avatar_url) as response:
                    if response.status == 200:
                        with open('profile_picture.png', 'wb') as f:
                            f.write(await response.read())
                # Send the profile picture to the channel and ping the user
                await channel.send(content=f'<@{USER_ID}>', file=discord.File('profile_picture.png'))
                await bot.close()

bot.run(TOKEN)
