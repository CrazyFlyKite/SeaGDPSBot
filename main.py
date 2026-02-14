import logging

from discord import Intents, Interaction, Game, Status
from discord.app_commands import AppCommandError, MissingRole, MissingAnyRole, NoPrivateMessage,CommandOnCooldown
from discord.ext.commands import Bot

from commands.add_group import AddGroup
from commands.edit_group import EditGroup
from commands.move_group import MoveGroup
from commands.remove_group import RemoveGroup
from decorators import log_command
from embeds import embed, error_embed
from setup_logging import setup_logging
from utilities import *

# Setup logging
if IS_NAS:
	logging.basicConfig(level=logging.DEBUG, format=LOGGING_FORMAT)
else:
	setup_logging(level=logging.DEBUG, logging_format=LOGGING_FORMAT)

# Setup Bot
intents: Intents = Intents.default()
intents.message_content = True  # NOQA
bot: Bot = Bot(command_prefix='/', intents=intents, activity=Game(name='SeaGDPS'), status=Status.do_not_disturb)
bot.remove_command('help')


# Startup
@bot.event
async def on_ready() -> None:
	logging.info(f'@{bot.user.name} is now running!')

	try:
		logging.info(f'Commands synced: {', '.join([cmd.name for cmd in await bot.tree.sync()])}')
	except Exception as exception:
		logging.error(f'Failed to sync commands: {exception}')


@bot.tree.error
async def on_app_command_error(interaction: Interaction, error: AppCommandError) -> None:
	if isinstance(error, (MissingRole, MissingAnyRole)):
		await interaction.response.send_message(embed=error_embed('You don\'t have the required role to use this command!'), ephemeral=True)
	elif isinstance(error, NoPrivateMessage):
		await interaction.response.send_message(embed=error_embed('You can\'t use this command in Direct Messages!'), ephemeral=True)
	elif isinstance(error, CommandOnCooldown):
		await interaction.response.send_message(embed=error_embed('You can\'t use this command that fast!'), ephemeral=True)
	else:
		logging.critical(f'Command Error: {error}')


# Commands
@bot.tree.command(name='info', description='Show information about the bot')
@log_command
async def info(interaction: Interaction) -> None:
	await interaction.response.send_message(embed=embed(description=INFORMATION_MESSAGE), ephemeral=True)


# Run
def main() -> None:
	bot.tree.add_command(AddGroup())
	bot.tree.add_command(RemoveGroup())
	bot.tree.add_command(MoveGroup())
	bot.tree.add_command(EditGroup())
	bot.run(TOKEN)


if __name__ == '__main__':
	main()
