import discord
import os
import aiohttp
import logging
from github import Github
from requests_oauthlib import OAuth1Session
from datetime import datetime
import json

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

LOG_FILE = "logs.json"
MAX_LOG_ENTRIES = 5

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class DiscordBot(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.github = Github(GITHUB_TOKEN)

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        try:
            guild = self.get_guild(SERVER_ID)
            if guild is None:
                return

            channel = guild.get_channel(CHANNEL_ID)
            if channel is None:
                return

            last_message = await self.get_last_message_from_user(channel, USER_ID)

            if last_message and "stop" in last_message.content.lower():
                await channel.send(content="Bot is currently stopped.")
                return
            elif last_message and any(keyword in last_message.content.lower() for keyword in ["go", "continue", "resume"]):
                await self.execute_bot_logic(guild, channel)

        except Exception as e:
            await channel.send(content=f"An error occurred: {e}")

        finally:
            await self.close()

    async def get_last_message_from_user(self, channel, user_id):
        async for message in channel.history(limit=10):
            if message.author.id == user_id:
                return message
        return None

    async def execute_bot_logic(self, guild, channel):
        user = guild.get_member(USER_ID)
        if user is None:
            return

        avatar_url = user.avatar.replace(size=1024, format='png').url if user.avatar else user.default_avatar.url
        old_avatar_url = self.get_previous_avatar_url()

        if avatar_url == old_avatar_url:
            await channel.send(content='Profile picture has not changed yet. No updates.')
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as response:
                    if response.status == 200:
                        file_path = 'pfp.png'
                        image_data = await response.read()

                        with open(file_path, 'wb') as f:
                            f.write(image_data)

                        self.save_current_avatar_url(avatar_url)

                        await channel.send(content='Profile picture updated', file=discord.File(file_path))

                        await self.upload_to_github(file_path, WEBSITE_FILE_PATH, repo_name=WEBSITE_REPO_NAME)
                        await self.upload_to_twitter(file_path)

                        os.remove(file_path)

        log_details = {
            "timestamp": datetime.now().isoformat(),
            "event": "Bot execution",
            "success": True,
            "details": {
                "guild": guild.name,
                "user": user.name,
                "channel": channel.name
            }
        }
        self.log_bot_run(log_details)

    def get_previous_avatar_url(self):
        try:
            repo = self.github.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
            contents = repo.get_contents(AVATAR_URL_FILE_PATH)
            return contents.decoded_content.decode()
        except Exception:
            return None

    def save_current_avatar_url(self, avatar_url):
        try:
            repo = self.github.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
            contents = repo.get_contents(AVATAR_URL_FILE_PATH)
            repo.update_file(contents.path, "Update avatar URL", avatar_url, contents.sha)
        except Exception:
            pass

    async def upload_to_github(self, file_path, github_path, repo_name=REPO_NAME):
        try:
            repo = self.github.get_repo(f"{REPO_OWNER}/{repo_name}")
            with open(file_path, 'rb') as file:
                content = file.read()
            contents = repo.get_contents(github_path)
            repo.update_file(contents.path, "Update profile picture", content, contents.sha)
        except Exception:
            pass

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
                files = {"media": file}
                response = oauth.post(url, files=files)

            media_id = response.json()["media_id_string"]

            url = "https://api.twitter.com/1.1/account/update_profile_image.json"
            params = {"media_id": media_id}
            response = oauth.post(url, params=params)
        except Exception:
            pass

    def log_bot_run(self, details):
        logs = {"cleanup_logs": [], "bot_logs": []}

        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as file:
                logs = json.load(file)

        if 'bot_logs' not in logs:
            logs['bot_logs'] = []

        logs["bot_logs"].append(details)

        if len(logs["bot_logs"]) > MAX_LOG_ENTRIES:
            logs["bot_logs"] = logs["bot_logs"][-MAX_LOG_ENTRIES:]

        with open(LOG_FILE, "w") as file:
            json.dump(logs, file, indent=4)


if __name__ == "__main__":
    bot = DiscordBot(intents=intents)
    bot.run(DISCORD_TOKEN)
