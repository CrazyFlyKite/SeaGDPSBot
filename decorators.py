import logging
from functools import wraps
from inspect import signature
from typing import Callable

from discord import Interaction
from discord.app_commands import describe

from database import execute_get
from embeds import error_embed
from utilities import DESCRIBED_PARAMETERS


def log_command(command: Callable) -> Callable:
	@wraps(command)
	async def wrapper(*args, **kwargs) -> None:
		try:
			interaction: Interaction = args[1]
		except IndexError:
			interaction = args[0]

		channel_name: str = interaction.channel.name if interaction.guild else f'Direct Messages'
		logging.debug(f'@{interaction.user.name} used the \"/{interaction.command.qualified_name}\" command in {channel_name}.')

		await command(*args, **kwargs)

	return wrapper


def limit_command(command: Callable) -> Callable:
	@wraps(command)
	async def wrapper(*args, **kwargs) -> None:
		try:
			interaction: Interaction = args[1]
		except IndexError:
			interaction = args[0]

		if interaction.channel.id in [channel[0] for channel in await execute_get('SELECT channel FROM settings')]:
			await command(*args, **kwargs)
		else:
			await interaction.response.send_message(embed=error_embed('You cannot use my commands in this channel!'), ephemeral=True)

	return wrapper


def smart_describe() -> Callable:
	def decorator(command: Callable) -> Callable:
		return describe(**{
			key: value for key, value in DESCRIBED_PARAMETERS.items() if key in signature(command).parameters
		})(command)

	return decorator
