from discord import Interaction
from discord.app_commands import checks, command, guild_only, autocomplete, rename, Group

from database import execute_get, execute_write
from decorators import log_command, limit_command, smart_describe
from embeds import success_embed, error_embed
from help_functions import level_autocomplete, player_name_autocomplete
from utilities import *


class RemoveGroup(Group, name='remove'):
	@command(name='level', description='Remove a level from the Demonlist')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def remove_level(self, interaction: Interaction, level_id: int) -> None:
		result = await execute_get('''
	    SELECT d.placement, d.level_name, p.player_name
	    FROM demonlist d
	    LEFT JOIN creators c ON d.level_id = c.level_id AND c.is_publisher = TRUE
	    LEFT JOIN players p ON c.player_id = p.player_id
	    WHERE d.level_id = %s
	    ''', (level_id,))

		if not result:
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		placement, name, publisher = result[0]
		publisher = publisher or 'Unknown'

		await execute_write('DELETE FROM demonlist WHERE level_id = %s', (level_id,))
		await execute_write('UPDATE demonlist SET placement = placement - 1 WHERE placement > %s ORDER BY placement ASC', (placement,))
		await interaction.response.send_message(embed=success_embed(f'\"**{name}**\" by {publisher} removed from the Demonlist!'))

	@command(name='creator', description='Remove a creator from a level')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete, creator=player_name_autocomplete)
	@smart_describe()
	@log_command
	async def remove_creator(self, interaction: Interaction, level_id: LevelIDInt, creator: str) -> None:
		result = await execute_get('''
        SELECT d.level_name, p.player_name
        FROM demonlist d
        LEFT JOIN creators c ON d.level_id = c.level_id AND c.is_publisher = 1
        LEFT JOIN players p ON c.player_id = p.player_id
        WHERE d.level_id = %s
	    ''', (level_id,))

		if not result:
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		level_name, publisher = result[0]

		if not (player_data := await execute_get('SELECT player_id, player_name FROM players WHERE player_name = %s', (creator,))):
			return await interaction.response.send_message(embed=error_embed(f'Player **{creator}** not found!'), ephemeral=True)

		player_id, player_name = player_data[0]
		is_publisher = await execute_get('SELECT is_publisher FROM creators WHERE level_id = %s AND player_id = %s', (level_id, player_id))

		if not is_publisher:
			return await interaction.response.send_message(embed=error_embed(f'**{player_name}** is not a creator of this level!'), ephemeral=True)

		if is_publisher[0][0]:
			return await interaction.response.send_message(embed=error_embed(f'**{player_name}** is the publisher! You must set a new publisher before removing.'), ephemeral=True)

		await execute_write('DELETE FROM creators WHERE level_id = %s AND player_id = %s', (level_id, player_id))
		await interaction.response.send_message(embed=success_embed(f'Removed creator **{player_name}** from \"**{level_name}**\" by {publisher}!'))

	@command(name='victor', description='Remove a victor from a level')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete, player_name=player_name_autocomplete)
	@smart_describe()
	@log_command
	async def remove_victor(self, interaction: Interaction, level_id: LevelIDInt, player_name: str) -> None:
		result = await execute_get('''
		SELECT d.level_name, p.player_name
        FROM demonlist d
        LEFT JOIN creators c ON d.level_id = c.level_id AND c.is_publisher = 1
        LEFT JOIN players p ON c.player_id = p.player_id
        WHERE d.level_id = %s
        ''', (level_id,))

		if not result:
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher = result[0]

		if not (player_data := await execute_get('SELECT player_id FROM players WHERE player_name = %s', (player_name,))):
			return await interaction.response.send_message(embed=error_embed(f'Player **{player_name}** is not registered yet! Use `/add player` first .'), ephemeral=True)

		record_check = await execute_get('SELECT is_verifier FROM records WHERE level_id = %s AND player_id = %s', (level_id, player_data[0][0]))

		if not record_check:
			return await interaction.response.send_message(embed=error_embed(f'**{player_name}** doesn\'t have a record on \"**{name}**\" by {publisher}!'), ephemeral=True)

		if record_check[0][0] == 1:
			return await interaction.response.send_message(embed=error_embed('You can\'t remove the verifier!'), ephemeral=True)

		await execute_write('DELETE FROM records WHERE level_id = %s AND player_id = %s', (level_id, player_data[0][0]))
		await interaction.response.send_message(embed=success_embed(f'Removed a victor **{player_name}** from \"**{name}**\" by {publisher}!'))
