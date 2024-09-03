import discord
import os
import logging

logging.basicConfig(level=logging.DEBUG)

DTOKEN = os.getenv("DTOKEN")
GITHUB_TOKEN = os.getenv("GTOKEN")
USER_ID = 849456491131043840
GUILD_NAME = "hutlaw's server"
CHANNEL_NAME = "bot-stuff"
REPO_NAME = "hutlaw.github.io"
IMAGE_PATH = "images/pfp.png"

class DiscordBot(discord.Client):
    async def on_ready(self):
        logging.info(f"Logged in as {self.user}")

        guild = discord.utils.get(self.guilds, name=GUILD_NAME)
        logging.debug(f"Guild found: {guild.name if guild else 'None'}")

        if guild:
            channel = discord.utils.get(guild.text_channels, name=CHANNEL_NAME)
            logging.debug(f"Channel found: {channel.name if channel else 'None'}")

            if channel:
                members = [member async for member in guild.fetch_members()]
                logging.debug("Members in the guild:")
                for member in members:
                    logging.debug(f"Member: {member.name}, ID: {member.id}")
                    if member.id == USER_ID:
                        await self.wait_for_command(channel, member)
                        return
                logging.error("User not found. Check USER_ID.")
            else:
                logging.error(f"Channel '{CHANNEL_NAME}' not found in guild '{GUILD_NAME}'.")
        else:
            logging.error(f"Guild '{GUILD_NAME}' not found.")

    async def wait_for_command(self, channel, user):
        await channel.send(f"{user.mention} The bot is ready to accept your command.")
        try:
            msg = await self.wait_for(
                'message',
                check=lambda message: message.author == user and message.channel == channel,
                timeout=1200.0  # 20 minutes
            )
            if msg.content.lower() == "!update":
                await self.update_profile_picture(channel)
        except discord.errors.NotFound:
            logging.error("Message not found during waiting.")
        except Exception as e:
            logging.error(f"Error while waiting for command: {str(e)}")

    async def update_profile_picture(self, channel):
        await channel.send("Updating profile picture...")
        try:
            self.upload_to_github('pfp.png', IMAGE_PATH, REPO_NAME)
            await channel.send("Profile picture updated successfully!")
        except Exception as e:
            logging.error(f"Failed to update profile picture: {str(e)}")
            await channel.send(f"Failed to update profile picture: {str(e)}")

    async def upload_to_github(self, file_path, github_path, repo_name):
        from github import Github

        g = Github(GITHUB_TOKEN)
        repo = g.get_user().get_repo(repo_name)
        with open(file_path, 'rb') as file:
            content = file.read()

        try:
            file = repo.get_contents(github_path)
            repo.update_file(file.path, "Update profile picture", content, file.sha)
        except Exception as e:
            logging.error(f"Failed to update file on GitHub: {str(e)}")
            raise

if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.members = True
    bot = DiscordBot(intents=intents)
    bot.run(DTOKEN)
