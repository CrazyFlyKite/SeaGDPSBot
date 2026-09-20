from discord.app_commands import command, guild_only, autocomplete, Group

from database import execute_get, execute_write
from decorators import log_command, limit_command, restrict_command, smart_describe
from embeds import success_embed, error_embed
from help_functions import player_name_autocomplete


class BanGroup(Group, name='ban'):
	async def _set_ban(self, interaction, player_name: str, banned: bool) -> None:
		if not (player_data := await execute_get('SELECT player_id, is_banned FROM players WHERE player_name = %s', (player_name,))):
			return await interaction.response.send_message(embed=error_embed(f'Player **{player_name}** not found!'), ephemeral=True)

		player_id, is_banned = player_data[0]
		action: str = 'banned' if banned else 'unbanned'

		if is_banned == banned:
			return await interaction.response.send_message(embed=error_embed(f'**{player_name}** is already {action}!'), ephemeral=True)

		await execute_write('UPDATE players SET is_banned = %s WHERE player_id = %s', (banned, player_id))
		await interaction.response.send_message(embed=success_embed(f'**{player_name}** was {action}!'), ephemeral=True)

	@command(name='add', description='Ban a player')
	@guild_only()
	@limit_command
	@restrict_command()
	@autocomplete(player_name=player_name_autocomplete)
	@smart_describe()
	@log_command
	async def ban_add(self, interaction, player_name: str) -> None:
		await self._set_ban(interaction, player_name, True)

	@command(name='remove', description='Unban a player')
	@guild_only()
	@limit_command
	@restrict_command()
	@autocomplete(player_name=player_name_autocomplete)
	@smart_describe()
	@log_command
	async def ban_remove(self, interaction, player_name: str) -> None:
		await self._set_ban(interaction, player_name, False)
