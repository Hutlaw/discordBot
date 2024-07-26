# bot.py

import discord
import os
import aiohttp
import asyncio
import requests
from base64 import b64encode
import json

# Retrieve the bot token and GitHub token from environment variables (GitHub secrets)
DISCORD_TOKEN = os.getenv('DToken')
GITHUB_TOKEN = os.getenv('GToken')

# Define the server and channel IDs
SERVER_ID = 1143308869817356428
CHANNEL_ID = 1266202982182162482
USER_ID = 849456491131043840

# Define your GitHub repository details
REPO_OWNER = "hutlaw"  # Replace with your GitHub username
REPO_NAME = "discordBot"  # Replace with your GitHub repository name
GITHUB_FILE_PATH = "pfp.png"  # File path in the repository

# Additional repository details
WEBSITE_REPO_NAME = "hutlaw.github.io"
WEBSITE_FILE_PATH = "pfp.png"  # Path in the additional repository

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
                        file_path = 'pfp.png'
                        with open(file_path, 'wb') as f:
                            f.write(await response.read())

                        print('Profile picture downloaded')

                        # Send the profile picture to the channel and ping the user
                        await channel.send(content=f'<@{USER_ID}>', file=discord.File(file_path))
                        print('Profile picture sent to channel')

                        # Upload the profile picture to GitHub
                        await self.upload_to_github(file_path, GITHUB_FILE_PATH)

                        # Upload to the second repository
                        await self.upload_to_github(file_path, WEBSITE_FILE_PATH, repo_name=WEBSITE_REPO_NAME)

                        # Update GitHub profile picture
                        await self.update_github_profile_picture(file_path)

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

    async def upload_to_github(self, file_path, file_path_in_repo, repo_name=None):
        """Upload a file to a specified GitHub repository."""
        try:
            repo_name = repo_name or REPO_NAME  # Default to the main repo if none is specified
            url = f"https://api.github.com/repos/{REPO_OWNER}/{repo_name}/contents/{file_path_in_repo}"
            headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            }

            # Try to get the SHA of the existing file
            response = requests.get(url, headers=headers)
            sha = None

            if response.status_code == 200:
                # File exists, get the SHA
                sha = response.json().get('sha')
                print(f'Existing file SHA: {sha}')
            elif response.status_code == 404:
                # File does not exist, will create a new one
                print('No existing file found. A new file will be created.')

            # Prepare the content to be uploaded
            with open(file_path, "rb") as file:
                content = b64encode(file.read()).decode("utf-8")

            # Prepare the data payload
            data = {
                "message": f"Update {file_path_in_repo}",
                "committer": {
                    "name": "Your Name",  # Replace with your GitHub username
                    "email": "your-email@example.com"  # Replace with your GitHub email
                },
                "content": content,
                "branch": "main"  # Replace with your target branch name
            }

            if sha:
                # Include SHA if replacing an existing file
                data["sha"] = sha

            # Send the request to upload the file
            response = requests.put(url, headers=headers, data=json.dumps(data))

            if response.status_code in [200, 201]:
                print(f'Profile picture uploaded to {repo_name} successfully.')
            else:
                print(f'Failed to upload to {repo_name}: {response.status_code} {response.content}')

        except Exception as e:
            print(f'Error uploading to {repo_name}: {e}')

    async def update_github_profile_picture(self, file_path):
        """Update GitHub profile picture using the uploaded image."""
        try:
            url = "https://api.github.com/user"
            headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            }

            # Read the image file to bytes
            with open(file_path, "rb") as file:
                image_data = file.read()

            # Prepare data for profile picture update
            data = {
                "avatar_url": b64encode(image_data).decode("utf-8")
            }

            # Send PATCH request to update GitHub profile picture
            response = requests.patch(url, headers=headers, data=json.dumps(data))

            if response.status_code == 200:
                print('GitHub profile picture updated successfully.')
            else:
                print(f'Failed to update GitHub profile picture: {response.status_code} {response.content}')

        except Exception as e:
            print(f'Error updating GitHub profile picture: {e}')

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
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
