import os
from io import BytesIO
from typing import Optional

from PIL import Image
from discord import Interaction, Attachment
from discord.app_commands import command, guild_only, autocomplete, rename, Group

from database import execute_get, execute_write
from decorators import log_command, limit_command, restrict_command, smart_describe
from embeds import success_embed, error_embed
from help_functions import level_autocomplete
from utilities import *


class SetGroup(Group, name='set'):
	@command(name='thumbnail', description='Add, remove or edit the thumbnail to a level')
	@guild_only()
	@limit_command
	@restrict_command(arg='level_id')
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def set_thumbnail(self, interaction: Interaction, level_id: LevelIDInt, thumbnail: Optional[Attachment] = None) -> None:
		await interaction.response.defer()

		result = await execute_get('''
		SELECT l.level_name, p.player_name, l.has_thumbnail
        FROM levels l
        LEFT JOIN creators c ON l.level_id = c.level_id AND c.is_publisher = TRUE
        LEFT JOIN players p ON c.player_id = p.player_id
        WHERE l.level_id = %s
        ''', (level_id,))

		if not result:
			return await interaction.followup.send(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, has_thumbnail = result[0]
		file_path: str = os.path.join(THUMBNAIL_PATH, f'{level_id}.jpg')

		if not thumbnail:
			if os.path.exists(file_path):
				os.remove(file_path)
				await execute_write('UPDATE levels SET has_thumbnail = %s WHERE level_id = %s', (False, level_id))
				return await interaction.followup.send(embed=success_embed(f'Removed thumbnail from \"**{name}**\" by {publisher}!'), ephemeral=False)
			else:
				return await interaction.followup.send(embed=error_embed(f'**{name}** has no thumbnail to remove!'), ephemeral=True)

		if not (thumbnail.filename.lower().endswith(ALLOWED_EXTENSIONS) and thumbnail.content_type in ALLOWED_TYPES):
			return await interaction.followup.send(embed=error_embed(f'Only {', '.join(f'**{ext}**' for ext in ALLOWED_EXTENSIONS)} files are allowed!'), ephemeral=True)

		try:
			image = Image.open(BytesIO(await thumbnail.read()))
			image.load()

			if image.mode in ('RGBA', 'P'):
				image = image.convert('RGB')

			image.save(file_path, format='JPEG', quality=95)
			await execute_write('UPDATE levels SET has_thumbnail = %s WHERE level_id = %s', (True, level_id))
			await interaction.followup.send(embed=success_embed(f'Set a thumbnail for \"**{name}**\" by {publisher}!'), ephemeral=False)
		except Exception as exception:
			await interaction.followup.send(embed=error_embed(f'System Error: {exception}'), ephemeral=True)

	@command(name='showcase', description='Add, remove or edit the showcase of a level')
	@guild_only()
	@limit_command
	@restrict_command(arg='level_id')
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def set_showcase(self, interaction: Interaction, level_id: LevelIDInt, showcase: Optional[str] = None) -> None:
		result = await execute_get('''
		SELECT l.level_name, p.player_name, l.showcase
        FROM levels l
        LEFT JOIN creators c ON l.level_id = c.level_id AND c.is_publisher = TRUE
        LEFT JOIN players p ON c.player_id = p.player_id
        WHERE l.level_id = %s
        ''', (level_id,))

		if not result:
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, current_showcase = result[0]

		if not showcase:
			if not current_showcase:
				return await interaction.response.send_message(embed=error_embed(f'\"**{name}**\" by {publisher} already has no showcase video!'), ephemeral=True)

			await execute_write('UPDATE levels SET showcase = %s WHERE level_id = %s', (None, level_id))
			return await interaction.response.send_message(embed=success_embed(f'Removed showcase from \"**{name}**\" by {publisher}!'), ephemeral=False)

		await execute_write('UPDATE levels SET showcase = %s WHERE level_id = %s', (showcase, level_id))
		await interaction.response.send_message(embed=success_embed(f'Updated the showcase for \"**{name}**\" by {publisher}!'), ephemeral=False)
