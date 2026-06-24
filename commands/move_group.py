from discord import Interaction
from discord.app_commands import command, guild_only, autocomplete, rename, Group

from database import execute_get, execute_write
from decorators import log_command, limit_command, restrict_command, smart_describe
from embeds import error_embed, success_embed
from help_functions import level_autocomplete
from utilities import *


class MoveGroup(Group, name='move'):
	@command(name='level', description='Move a level to a new placement')
	@guild_only()
	@limit_command
	@restrict_command(arg='level_id')
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def move_level(self, interaction: Interaction, level_id: LevelIDInt, new_placement: PlacementInt) -> None:
		result = await execute_get('''
		SELECT l.list_id, l.placement, l.level_name, p.player_name
	    FROM levels l
	    LEFT JOIN creators c ON l.level_id = c.level_id AND c.is_publisher = TRUE
	    LEFT JOIN players p ON c.player_id = p.player_id
	    WHERE l.level_id = %s
	    ''', (level_id,))

		if not result:
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		list_id, old_placement, name, publisher = result[0]

		if new_placement == old_placement:
			return await interaction.response.send_message(embed=error_embed('Level is already at that placement!'), ephemeral=True)

		max_placement: int = (await execute_get('SELECT MAX(placement) FROM levels WHERE list_id = %s', (list_id,)))[0][0]

		if not (1 <= new_placement <= max_placement):
			return await interaction.response.send_message(embed=error_embed(f'Placement must be between **1** and **{max_placement}**!'), ephemeral=True)

		await execute_write('UPDATE levels SET placement = 0 WHERE level_id = %s', (level_id,))

		if new_placement < old_placement:
			await execute_write('''
			UPDATE levels
			SET placement = placement + 1
			WHERE list_id = %s 
			AND placement >= %s
			AND placement < %s
			ORDER BY placement DESC;
			''', (list_id, new_placement, old_placement))
		else:
			await execute_write('''
			UPDATE levels
			SET placement = placement - 1
			WHERE list_id = %s
			AND placement > %s
			AND placement <= %s
			ORDER BY placement ASC;
			''', (list_id, old_placement, new_placement))

		await execute_write('UPDATE levels SET placement = %s WHERE level_id = %s', (new_placement, level_id))
		await interaction.response.send_message(embed=success_embed(f'\"**{name}**\" by {publisher} moved from **#{old_placement}** to **#{new_placement}** on the list!'))
