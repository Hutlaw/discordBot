# bot.py

import discord
import os
import aiohttp
import asyncio
import requests
from base64 import b64encode
import json

DISCORD_TOKEN = os.getenv('DToken')
GITHUB_TOKEN = os.getenv('GToken')

SERVER_ID = 1143308869817356428
CHANNEL_ID = 1266202982182162482
USER_ID = 849456491131043840

REPO_OWNER = "hutlaw"
REPO_NAME = "discordBot"
GITHUB_FILE_PATH = "images/pfp.png"  # Update to images folder

WEBSITE_REPO_NAME = "hutlaw.github.io"
WEBSITE_FILE_PATH = "images/pfp.png"  # Update to images folder

intents = discord.Intents.default()
intents.members = True

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

            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            print(f'User avatar URL: {avatar_url}')

            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as response:
                    if response.status == 200:
                        file_path = 'pfp.png'
                        with open(file_path, 'wb') as f:
                            f.write(await response.read())

                        print('Profile picture downloaded')

                        await channel.send(content='Profile picture updated', file=discord.File(file_path))
                        print('Profile picture sent to channel')

                        await self.upload_to_github(file_path, GITHUB_FILE_PATH)
                        await self.upload_to_github(file_path, WEBSITE_FILE_PATH, repo_name=WEBSITE_REPO_NAME)
                        await self.update_github_profile_picture(file_path)

                        os.remove(file_path)
                    else:
                        await channel.send(
                            content='Failed to retrieve profile picture.',
                            embed=discord.Embed(description="Failed to retrieve profile picture.")
                        )
                        print('Failed to retrieve profile picture')

        except Exception as e:
            print(f'Error: {e}')

        finally:
            await self.close()

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
                print(f'Existing file SHA: {sha}')
            elif response.status_code == 404:
                print('No existing file found. A new file will be created.')

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
                print(f'Profile picture uploaded to {repo_name} successfully.')
            else:
                print(f'Failed to upload to {repo_name}: {response.status_code} {response.content}')

        except Exception as e:
            print(f'Error uploading to {repo_name}: {e}')

    async def update_github_profile_picture(self, file_path):
        try:
            url = "https://api.github.com/user"
            headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            }

            with open(file_path, "rb") as file:
                image_data = file.read()

            data = {
                "avatar_url": b64encode(image_data).decode("utf-8")
            }

            response = requests.patch(url, headers=headers, data=json.dumps(data))

            if response.status_code == 200:
                print('GitHub profile picture updated successfully.')
            else:
                print(f'Failed to update GitHub profile picture: {response.status_code} {response.content}')

        except Exception as e:
            print(f'Error updating GitHub profile picture: {e}')

    async def setup_hook(self):
        self.bg_task = self.loop.create_task(self.timeout_bot())

    async def timeout_bot(self):
        await asyncio.sleep(60)
        if not self.is_closed():
            print('Timeout reached, closing bot')
            await self.close()

async def main():
    bot = DiscordBot(intents=intents)
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())