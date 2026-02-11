from discord import Interaction, Colour
from discord.app_commands import checks, command, guild_only, autocomplete, rename, Group

from database import execute_get, execute_write
from decorators import log_command, limit_command, smart_describe
from embeds import embed, success_embed, error_embed
from help_functions import level_autocomplete
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
		if not (result := await execute_get('SELECT placement, name, publisher FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		placement, name, publisher = result[0]
		await execute_write('DELETE FROM demonlist WHERE id = %s', (level_id,))
		await execute_write('UPDATE demonlist SET placement = placement - 1 WHERE placement > %s ORDER BY placement ASC', (placement,))
		await interaction.response.send_message(embed=success_embed(f'\"**{name}**\" by {publisher} removed from the Demonlist!'))

	@command(name='creator', description='Remove a creator from a level')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def remove_creator(self, interaction: Interaction, level_id: LevelIDInt, creator: str) -> None:
		if not (result := await execute_get('SELECT name, publisher, creators FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, creators = result[0]
		creators = json.loads(creators)
		actual_creator: Optional[str] = next((c for c in creators if c.lower() == creator.lower()), None)

		if not actual_creator:
			return await interaction.response.send_message(embed=error_embed('This creator is not in the list!'), ephemeral=True)

		if len(creators) <= 1:
			return await interaction.response.send_message(embed=error_embed('You cannot remove the only creator!'), ephemeral=True)

		creators.remove(actual_creator)

		await execute_write(
			'UPDATE demonlist SET creators = %s, publisher = %s WHERE id = %s',
			(json.dumps(creators), creators[0] if actual_creator == publisher else publisher, level_id)
		)
		await interaction.response.send_message(embed=success_embed(f'Removed a creator **{actual_creator}** from \"**{name}**\" by {publisher}!'))

	@command(name='victor', description='Removes a victor from the victors list')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def remove_victor(self, interaction: Interaction, level_id: LevelIDInt, player_name: str) -> None:
		if not (result := await execute_get('SELECT name, publisher, victors FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, victors = result[0]
		victors = json.loads(victors)
		actual_player: Optional[Dict[str, str | int]] = next((v for v in victors if v['name'].lower() == player_name.lower()), None)

		if player_name.lower() not in [player.get('name').lower() for player in victors]:
			return await interaction.response.send_message(embed=error_embed('This victor is not in the list!'), ephemeral=True)

		victors.remove(actual_player)
		await execute_write('UPDATE demonlist SET victors = %s WHERE id = %s', (json.dumps(victors), level_id))
		await interaction.response.send_message(
			embed=success_embed(f'Removed a victor **{actual_player.get('name')}** from \"**{name}**\" by {publisher}!')
		)
