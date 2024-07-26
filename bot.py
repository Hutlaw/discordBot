# bot.py

import discord
import os
import aiohttp
import asyncio
import requests
from base64 import b64encode
import json
from discord.ext import tasks

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
GITHUB_FILE_PATH = "pfp.png"  # File path in the main repository

# Additional repository details for uploading the image
WEBSITE_REPO_NAME = "hutlaw.github.io"
WEBSITE_FILE_PATH = "images/pfp.png"  # Path in the images folder of the additional repository

# Create an instance of the bot with necessary intents
intents = discord.Intents.default()
intents.members = True  # Enable the members intent

class DiscordBot(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.profile_picture_task.start()  # Start the scheduled task

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

            # Download and update profile picture
            await self.update_profile_picture(channel, avatar_url)

        except Exception as e:
            print(f'Error: {e}')

    async def update_profile_picture(self, channel, avatar_url):
        """Download and update the profile picture."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as response:
                    if response.status == 200:
                        file_path = 'pfp.png'
                        with open(file_path, 'wb') as f:
                            f.write(await response.read())

                        print('Profile picture downloaded')

                        # Send the profile picture update message
                        await channel.send(content="Profile picture updated")
                        print('Profile picture update message sent to channel')

                        # Upload the profile picture to GitHub
                        await self.upload_to_github(file_path, GITHUB_FILE_PATH)

                        # Upload to the second repository's images folder
                        await self.upload_to_github(file_path, WEBSITE_FILE_PATH, repo_name=WEBSITE_REPO_NAME)

                        # Update GitHub profile picture
                        await self.update_github_profile_picture(file_path)

                        # Clean up the file after sending
                        os.remove(file_path)
                    else:
                        await channel.send(
                            content="Failed to retrieve profile picture.",
                            embed=discord.Embed(description="Failed to retrieve profile picture.")
                        )
                        print('Failed to retrieve profile picture')

        except Exception as e:
            print(f'Error in update_profile_picture: {e}')

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

            # Prepare the headers and payload for uploading
            headers["Content-Type"] = "image/png"  # Add content type
            response = requests.post(
                url,
                headers=headers,
                files={"avatar": ("pfp.png", image_data, "image/png")}
            )

            if response.status_code == 200:
                print('GitHub profile picture updated successfully.')
            else:
                print(f'Failed to update GitHub profile picture: {response.status_code} {response.content}')

        except Exception as e:
            print(f'Error updating GitHub profile picture: {e}')

    @tasks.loop(hours=1)
    async def profile_picture_task(self):
        """Task to update profile picture every hour."""
        try:
            guild = self.get_guild(SERVER_ID)
            if guild is None:
                print(f"Error: Guild with ID {SERVER_ID} not found.")
                return

            user = guild.get_member(USER_ID)
            if user is None:
                print(f"Error: User with ID {USER_ID} not found in guild.")
                return

            channel = guild.get_channel(CHANNEL_ID)
            if channel is None:
                print(f"Error: Channel with ID {CHANNEL_ID} not found in guild.")
                return

            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            print(f'Updating avatar for {user.name} with URL: {avatar_url}')
            await self.update_profile_picture(channel, avatar_url)
        except Exception as e:
            print(f'Error in profile_picture_task: {e}')

async def main():
    bot = DiscordBot(intents=intents)
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
