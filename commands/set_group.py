import os

from discord import Interaction, Attachment
from discord.app_commands import checks, command, guild_only, autocomplete, rename, Group

from database import execute_get, execute_write
from decorators import log_command, limit_command, smart_describe
from embeds import success_embed, error_embed
from help_functions import level_autocomplete
from utilities import *


class SetGroup(Group, name='set'):
	@command(name='thumbnail', description='Add, remove or edit the thumbnail to a level')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def set_thumbnail(self, interaction: Interaction, level_id: LevelIDInt, thumbnail: Optional[Attachment] = None) -> None:
		if not (result := await execute_get('SELECT name, publisher, has_thumbnail FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, has_thumbnail = result[0]
		file_path: str = os.path.join(THUMBNAILS_PATH, f'{level_id}.jpg')

		if not thumbnail:
			if os.path.exists(file_path):
				os.remove(file_path)
				await execute_write('UPDATE demonlist SET has_thumbnail = %s WHERE id = %s', (False, level_id))
				return await interaction.response.send_message(
					embed=success_embed(f'Removed thumbnail for \"**{name}**\" by {publisher}!'),
					ephemeral=False
				)
			else:
				return await interaction.response.send_message(embed=error_embed(f'**{name}** has no thumbnail to remove!'), ephemeral=True)

		if not (thumbnail.filename.lower().endswith('.jpg') and (thumbnail.content_type == 'image/jpeg')):
			return await interaction.response.send_message(embed=error_embed('Only **.jpg** files are allowed!'), ephemeral=True)

		try:
			await thumbnail.save(file_path)
			await execute_write('UPDATE demonlist SET has_thumbnail = %s WHERE id = %s', (True, level_id))
			await interaction.response.send_message(
				embed=success_embed(f'Successfully set a thumbnail for \"**{name}**\" by {publisher}!'),
				ephemeral=False
			)
		except Exception as e:
			await interaction.response.send_message(embed=error_embed(f'System Error: {str(e)}'), ephemeral=True)

	@command(name='showcase', description='Add, remove or edit the showcase of a level')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def set_showcase(self, interaction: Interaction, level_id: LevelIDInt, showcase: Optional[str] = None) -> None:
		if not (result := await execute_get('SELECT name, publisher, showcase FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, current_showcase = result[0]

		if not showcase:
			if not current_showcase:
				return await interaction.response.send_message(
					embed=error_embed(f'\"**{name}**\" by {publisher} already has no showcase video!'),
					ephemeral=True
				)

			await execute_write('UPDATE demonlist SET showcase = %s WHERE id = %s', (None, level_id))
			return await interaction.response.send_message(
				embed=success_embed(f'Removed showcase for \"**{name}**\" by {publisher}!'),
				ephemeral=False
			)

		if not ('youtube.com/' in showcase or 'youtu.be/' in showcase):
			return await interaction.response.send_message(embed=error_embed('Please provide a valid **YouTube** link!'), ephemeral=True)

		await execute_write('UPDATE demonlist SET showcase = %s WHERE id = %s', (showcase, level_id))
		await interaction.response.send_message(embed=success_embed(f'Updated the showcase for \"**{name}**\" by {publisher}!'), ephemeral=False)
