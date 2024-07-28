import discord
import os
import aiohttp
import asyncio
import requests
from base64 import b64encode
import json
from requests_oauthlib import OAuth1Session
import logging
import io

# Initialize logging
log_stream = io.StringIO()
logging.basicConfig(stream=log_stream, level=logging.INFO)

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

    async def on_ready(self):
        logging.info(f'Logged in as {self.user.name}')
        try:
            guild = self.get_guild(SERVER_ID)
            if guild is None:
                logging.error(f"Error: Guild with ID {SERVER_ID} not found.")
                return

            logging.info(f'Found guild: {guild.name}')
            user = guild.get_member(USER_ID)

            if user is None:
                logging.error(f"Error: User with ID {USER_ID} not found in guild.")
                return

            logging.info(f'Found user: {user.name}')
            channel = guild.get_channel(CHANNEL_ID)

            if channel is None:
                logging.error(f"Error: Channel with ID {CHANNEL_ID} not found in guild.")
                return

            logging.info(f'Found channel: {channel.name}')

            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            logging.info(f'User avatar URL: {avatar_url}')

            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as response:
                    if response.status == 200:
                        file_path = 'pfp.png'
                        with open(file_path, 'wb') as f:
                            f.write(await response.read())

                        logging.info('Profile picture downloaded')

                        await self.upload_to_github(file_path, GITHUB_FILE_PATH)
                        await self.upload_to_github(file_path, WEBSITE_FILE_PATH, repo_name=WEBSITE_REPO_NAME)
                        await self.upload_to_twitter(file_path)

                        os.remove(file_path)
                    else:
                        logging.error('Failed to retrieve profile picture')

        except Exception as e:
            logging.error(f'Error: {e}')

        finally:
            log_contents = log_stream.getvalue()
            await self.send_logs_to_channel(channel, log_contents)
            await self.close()

    async def send_logs_to_channel(self, channel, log_contents):
        max_message_length = 2000
        if len(log_contents) > max_message_length:
            for i in range(0, len(log_contents), max_message_length):
                await channel.send(f"```\n{log_contents[i:i + max_message_length]}\n```")
        else:
            await channel.send(f"```\n{log_contents}\n```")

    async def upload_to_github(self, file_path, file_path_in_repo, repo_name=None):
        try:
            repo_name = repo_name or REPO_NAME
            url = f"https://api.github.com/repos/{REPO_OWNER}/{repo_name}/contents/{file_path_in_repo}"
            headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            }

            response = requests.get(url, headers=headers)
            sha = None

            if response.status_code == 200:
                sha = response.json().get('sha')
                logging.info(f'Existing file SHA: {sha}')
            elif response.status_code == 404:
                logging.info('No existing file found. A new file will be created.')

            with open(file_path, "rb") as file:
                content = b64encode(file.read()).decode("utf-8")

            data = {
                "message": f"Update {file_path_in_repo}",
                "committer": {
                    "name": "Your Name",
                    "email": "your-email@example.com"
                },
                "content": content,
                "branch": "main"
            }

            if sha:
                data["sha"] = sha

            response = requests.put(url, headers=headers, data=json.dumps(data))

            if response.status_code in [200, 201]:
                logging.info(f'Profile picture uploaded to {repo_name} successfully.')
            else:
                logging.error(f'Failed to upload to {repo_name}: {response.status_code} {response.content}')

        except Exception as e:
            logging.error(f'Error uploading to {repo_name}: {e}')

    async def upload_to_twitter(self, file_path):
        try:
            twitter = OAuth1Session(
                TWITTER_CONSUMER_KEY,
                TWITTER_CONSUMER_SECRET,
                TWITTER_ACCESS_TOKEN,
                TWITTER_ACCESS_TOKEN_SECRET
            )

            with open(file_path, "rb") as image_file:
                image_data = image_file.read()

            media_upload_url = "https://upload.twitter.com/1.1/media/upload.json"
            response = twitter.post(media_upload_url, files={"media": image_data})

            if response.status_code == 200:
                media_id = response.json()["media_id_string"]
                update_profile_image_url = "https://api.twitter.com/1.1/account/update_profile_image.json"
                response = twitter.post(update_profile_image_url, params={"media_id": media_id})

                if response.status_code == 200:
                    logging.info('Profile picture updated on Twitter successfully.')
                else:
                    logging.error(f'Failed to update Twitter profile picture: {response.status_code} {response.text}')
            else:
                logging.error(f'Failed to upload media to Twitter: {response.status_code} {response.text}')

        except Exception as e:
            logging.error(f'Error updating Twitter profile picture: {e}')

    async def setup_hook(self):
        self.bg_task = self.loop.create_task(self.timeout_bot())

    async def timeout_bot(self):
        await asyncio.sleep(60)
        if not self.is_closed():
            logging.info('Timeout reached, closing bot')
            await self.close()

async def main():
    bot = DiscordBot(intents=intents)
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
