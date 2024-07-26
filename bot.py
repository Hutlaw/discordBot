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
        channel = guild.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f'<@{USER_ID}>')
            await bot.close()

bot.run(TOKEN)
