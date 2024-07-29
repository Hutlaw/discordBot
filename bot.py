import discord
import os
import aiohttp
import asyncio
from hashlib import md5
import logging
from github import Github
from requests_oauthlib import OAuth1Session

# Setup logging
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
GITHUB_FILE_PATH = "pfp.png"

WEBSITE_REPO_NAME = "hutlaw.github.io"
WEBSITE_FILE_PATH = "images/pfp.png"

intents = discord.Intents.default()
intents.members = True

class DiscordBot(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.github = Github(GITHUB_TOKEN)

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        try:
            guild = self.get_guild(SERVER_ID)
            if guild is None:
                raise ValueError(f"Guild with ID {SERVER_ID} not found.")

            logger.info(f'Found guild: {guild.name}')
            user = guild.get_member(USER_ID)
            if user is None:
                raise ValueError(f"User with ID {USER_ID} not found in guild.")

            logger.info(f'Found user: {user.name}')
            channel = guild.get_channel(CHANNEL_ID)
            if channel is None:
                raise ValueError(f"Channel with ID {CHANNEL_ID} not found in guild.")

            logger.info(f'Found channel: {channel.name}')
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            logger.info(f'User avatar URL: {avatar_url}')

            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as response:
                    if response.status == 200:
                        file_path = 'pfp.png'
                        image_data = await response.read()
                        new_hash = md5(image_data).hexdigest()
                        old_hash = self.get_previous_hash()

                        if new_hash == old_hash:
                            logger.info('Profile picture has not changed.')
                            await channel.send(content='Profile picture has not changed yet. No updates.')
                        else:
                            with open(file_path, 'wb') as f:
                                f.write(image_data)
                            self.save_current_hash(new_hash)
                            logger.info('Profile picture downloaded')
                            await channel.send(content='Profile picture updated', file=discord.File(file_path))

                            await self.upload_to_github(file_path, GITHUB_FILE_PATH)
                            await self.upload_to_github(file_path, WEBSITE_FILE_PATH, repo_name=WEBSITE_REPO_NAME)
                            await self.upload_to_twitter(file_path)
                            os.remove(file_path)
                    else:
                        raise Exception('Failed to retrieve profile picture.')

        except Exception as e:
            await channel.send(content=f'Error: {e}', embed=discord.Embed(description=str(e)))
            logger.error(f'Error: {e}')
        finally:
            await self.close()

    def get_previous_hash(self):
        try:
            repo = self.github.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
            contents = repo.get_contents("pfp_hash.txt")
            return contents.decoded_content.decode()
        except Exception as e:
            logger.error(f'Error getting previous hash: {e}')
            return None

    def save_current_hash(self, new_hash):
        try:
            repo = self.github.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
            contents = repo.get_contents("pfp_hash.txt")
            repo.update_file(contents.path, "Update profile picture hash", new_hash, contents.sha)
        except Exception as e:
            logger.error(f'Error saving current hash: {e}')

    async def upload_to_github(self, file_path, github_path, repo_name=REPO_NAME):
        try:
            repo = self.github.get_repo(f"{REPO_OWNER}/{repo_name}")
            with open(file_path, 'rb') as file:
                content = file.read()
            contents = repo.get_contents(github_path)
            repo.update_file(contents.path, "Update profile picture", content, contents.sha)
            logger.info(f'Profile picture uploaded to {repo_name} successfully.')
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
                files = {"media": file}
                response = oauth.post(url, files=files)

            media_id = response.json()["media_id_string"]
            url = "https://api.twitter.com/1.1/account/update_profile_image.json"
            params = {"media_id": media_id}
            response = oauth.post(url, params=params)

            if response.status_code == 200:
                logger.info('Profile picture updated on Twitter successfully.')
            else:
                raise Exception(f'Failed to update profile picture on Twitter: {response.text}')
        except Exception as e:
            logger.error(f'Error uploading to Twitter: {e}')

if __name__ == "__main__":
    bot = DiscordBot(intents=intents)
    bot.run(DISCORD_TOKEN)
