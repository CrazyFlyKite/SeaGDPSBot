import logging
from functools import wraps
from inspect import signature
from typing import Set, Optional, Callable

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


def restrict_command(arg: Optional[str] = None, lookup_by_list: Optional[bool] = False) -> Callable:
	def decorator(command) -> Callable:
		@wraps(command)
		async def wrapper(*args, **kwargs) -> None:
			interaction = args[1] if len(args) > 1 else args[0]

			if interaction.user.id == DEVELOPER_ID:
				return await command(*args, **kwargs)

			user_role_ids: Set[int] = {role.id for role in interaction.user.roles}

			if arg is None:
				result = await execute_get('SELECT DISTINCT moderator_role_id FROM lists')
				allowed_role_ids: Set[int] = {row[0] for row in result if row[0] is not None}

				if user_role_ids & allowed_role_ids:
					return await command(*args, **kwargs)
			else:
				if lookup_by_list:
					result = await execute_get('SELECT moderator_role_id FROM lists WHERE list_id = %s', (kwargs.get(arg),))
				else:
					result = await execute_get('SELECT li.moderator_role_id FROM levels l JOIN lists li ON l.list_id = li.list_id WHERE l.level_id = %s', (kwargs.get(arg),))

				if not result:
					return await interaction.response.send_message(embed=error_embed('Permission error occurred!'), ephemeral=True)

				if result[0][0] in user_role_ids:
					return await command(*args, **kwargs)

			return await interaction.response.send_message(embed=error_embed('You have no permissions to use this command!'), ephemeral=True)

		return wrapper

	return decorator


def smart_describe() -> Callable:
	def decorator(command: Callable) -> Callable:
		return describe(**{key: value for key, value in DESCRIBED_PARAMETERS.items() if key in signature(command).parameters})(command)

	return decorator
