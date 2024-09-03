import discord
import os
import aiohttp
import logging
from github import Github
from requests_oauthlib import OAuth1Session
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

DISCORD_TOKEN = os.getenv('DTOKEN')
GITHUB_TOKEN = os.getenv('GTOKEN')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
TWITTER_CONSUMER_KEY = os.getenv('TWITTER_CLIENT_ID')
TWITTER_CONSUMER_SECRET = os.getenv('TWITTER_CLIENT_SECRET')

SERVER_ID = 1143308869817356428
CHANNEL_ID = 1266202982182162482
USER_ID = 849456491131043840

REPO_OWNER = "hutlaw"
REPO_NAME = "discordBot"
AVATAR_URL_FILE_PATH = "avatar_url.txt"

WEBSITE_REPO_NAME = "hutlaw.github.io"
WEBSITE_FILE_PATH = "images/pfp.png"

intents = discord.Intents.default()
intents.messages = True

class DiscordBot(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.github = Github(GITHUB_TOKEN)

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        guild = self.get_guild(SERVER_ID)
        if not guild:
            logger.error("Guild not found.")
            await self.close()
            return

        channel = guild.get_channel(CHANNEL_ID)
        if not channel:
            logger.error("Channel not found.")
            await self.close()
            return

        user = guild.get_member(USER_ID)
        if not user:
            logger.error("User not found.")
            await self.close()
            return

        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        old_avatar_url = self.get_previous_avatar_url()

        if avatar_url == old_avatar_url:
            await channel.send(content='Profile picture has not changed. No updates.')
        else:
            await self.update_avatar(channel, avatar_url)

        await channel.send(content='Type `!continue` within 5 minutes to keep the bot active.')
        self.keep_alive_task = self.loop.create_task(self.wait_for_command(channel))

    async def update_avatar(self, channel, avatar_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as response:
                if response.status == 200:
                    file_path = 'pfp.png'
                    with open(file_path, 'wb') as f:
                        f.write(await response.read())

                    self.save_current_avatar_url(avatar_url)
                    await channel.send(content='Profile picture updated', file=discord.File(file_path))
                    await self.upload_to_github(file_path, WEBSITE_FILE_PATH, repo_name=WEBSITE_REPO_NAME)
                    await self.upload_to_twitter(file_path)
                    os.remove(file_path)
                else:
                    await channel.send(content='Failed to retrieve profile picture.')

    async def wait_for_command(self, channel):
        def check(m):
            return m.author.id == USER_ID and m.content.lower() == "!continue"

        try:
            await self.wait_for('message', timeout=300, check=check)
            await channel.send(content='Bot will remain active.')
        except asyncio.TimeoutError:
            await channel.send(content='No response received. Bot shutting down.')
            await self.close()

    def get_previous_avatar_url(self):
        try:
            repo = self.github.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
            contents = repo.get_contents(AVATAR_URL_FILE_PATH)
            return contents.decoded_content.decode()
        except Exception as e:
            logger.error(f'Error getting previous avatar URL: {e}')
            return None

    def save_current_avatar_url(self, avatar_url):
        try:
            repo = self.github.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
            contents = repo.get_contents(AVATAR_URL_FILE_PATH)
            repo.update_file(contents.path, "Update avatar URL", avatar_url, contents.sha)
        except Exception as e:
            logger.error(f'Error saving current avatar URL: {e}')

    async def upload_to_github(self, file_path, github_path, repo_name=REPO_NAME):
        try:
            repo = self.github.get_repo(f"{REPO_OWNER}/{repo_name}")
            with open(file_path, 'rb') as file:
                content = file.read()
            contents = repo.get_contents(github_path)
            repo.update_file(contents.path, "Update profile picture", content, contents.sha)
        except Exception as e:
            logger.error(f'Error uploading to GitHub: {e}')

    async def upload_to_twitter(self, file_path):
        try:
            oauth = OAuth1Session(
                TWITTER_CONSUMER_KEY,
                client_secret=TWITTER_CONSUMER_SECRET,
                resource_owner_key=TWITTER_ACCESS_TOKEN,
                resource_owner_secret=TWITTER_ACCESS_TOKEN_SECRET,
            )
            url = "https://upload.twitter.com/1.1/media/upload.json"
            with open(file_path, 'rb') as file:
                response = oauth.post(url, files={"media": file})

            media_id = response.json().get("media_id_string")
            if media_id:
                params = {"media_id": media_id}
                response = oauth.post("https://api.twitter.com/1.1/account/update_profile_image.json", params=params)

                if response.status_code == 200:
                    logger.info('Profile picture updated on Twitter successfully.')
                else:
                    logger.error(f'Failed to update profile picture on Twitter: {response.text}')
        except Exception as e:
            logger.error(f'Error uploading to Twitter: {e}')

if __name__ == "__main__":
    bot = DiscordBot(intents=intents)
    bot.run(DISCORD_TOKEN)
