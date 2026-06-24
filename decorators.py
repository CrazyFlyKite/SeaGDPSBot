import logging
from functools import wraps
from inspect import signature
from typing import Callable

from discord.app_commands import describe

from database import execute_get
from embeds import error_embed
from utilities import DESCRIBED_PARAMETERS, DEVELOPER_ID


def log_command(command: Callable) -> Callable:
	@wraps(command)
	async def wrapper(*args, **kwargs) -> None:
		interaction = args[1] if len(args) > 1 else args[0]

		channel_name: str = interaction.channel.name if interaction.guild else 'Direct Messages'
		logging.debug(f'@{interaction.user.name} used the \"/{interaction.command.qualified_name}\" command in {channel_name}.')

		await command(*args, **kwargs)

	return wrapper


def limit_command(command: Callable) -> Callable:
	@wraps(command)
	async def wrapper(*args, **kwargs) -> None:
		interaction = args[1] if len(args) > 1 else args[0]

		if interaction.channel.id in [channel[0] for channel in await execute_get('SELECT channel_id FROM channels')]:
			await command(*args, **kwargs)
		else:
			await interaction.response.send_message(embed=error_embed('You cannot use my commands in this channel!'), ephemeral=True)

	return wrapper


def restrict_command(level_id_arg: str) -> Callable:
	def decorator(command) -> Callable:
		@wraps(command)
		async def wrapper(*args, **kwargs) -> None:
			interaction = args[1] if len(args) > 1 else args[0]

			if interaction.user.id == DEVELOPER_ID:
				return await command(*args, **kwargs)

			if not (result := await execute_get('SELECT li.moderator_role_id FROM levels l JOIN lists li ON li.list_id = l.list_id WHERE l.level_id = %s', (kwargs.get(level_id_arg),))):
				return await interaction.response.send_message(embed=error_embed('This list doesn\'t exist!'), ephemeral=True)

			role_id = result[0][0]

			if role_id and any(r.id == role_id for r in interaction.user.roles):
				return await command(*args, **kwargs)

			return await interaction.response.send_message(embed=error_embed('You have no permissions to use this command!'), ephemeral=True)

		return wrapper

	return decorator


def smart_describe() -> Callable:
	def decorator(command: Callable) -> Callable:
		return describe(**{key: value for key, value in DESCRIBED_PARAMETERS.items() if key in signature(command).parameters})(command)

	return decorator
