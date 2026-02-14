from typing import Tuple

from discord import Interaction, Colour
from discord.app_commands import checks, choices, command, guild_only, autocomplete, rename, Group

from help_functions import level_autocomplete
from database import execute_get, execute_write
from decorators import log_command, limit_command, smart_describe
from embeds import embed, success_embed, error_embed
from utilities import *


class AddGroup(Group, name='add'):
	@command(name='level', description='Add a level to the Demonlist')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@choices(difficulty=DIFFICULTIES, rating=RATINGS)
	@smart_describe()
	@log_command
	async def add_level(self, interaction: Interaction, placement: PlacementInt, level_id: LevelIDInt, name: str, creators: str, verifier: str,
	                    difficulty: int, rating: int, list_percentage: PercentageInt) -> None:
		if await execute_get('SELECT name FROM demonlist WHERE id = %s', (level_id,)):
			return await interaction.response.send_message(embed=error_embed(f'Level with ID **{level_id}** already exists!'), ephemeral=True)

		publisher: str = creators.split(',')[0].strip()
		creators_list: str = json.dumps([s.strip() for s in creators.split(',')])
		max_placement: int = (await execute_get('SELECT MAX(placement) FROM demonlist') or 0)[0][0] + 1
		list_context: List[Tuple[int, str]] = await execute_get('SELECT placement, name FROM demonlist WHERE placement IN (10, 25)')

		if not (1 <= placement <= max_placement):
			return await interaction.response.send_message(
				embed=error_embed(f'The placement be between **1** and **{max_placement}**!'),
				ephemeral=True
			)

		await execute_write('UPDATE demonlist SET placement = placement + 1 WHERE placement >= %s ORDER BY placement DESC', (placement,))
		await execute_write('''
	    INSERT INTO demonlist
	    (id, placement, name, publisher, creators, verifier, difficulty, rating, list_percentage, victors)
	    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
	    ''', (level_id, placement, name, publisher, creators_list, verifier, difficulty, rating, list_percentage, json.dumps([])))

		audit_description: str = ''
		ctx_map: Dict[int, str] = {row[0]: row[1] for row in list_context}

		if pushed_10 := ctx_map.get(10) if placement <= 10 else None:
			audit_description += f'Pushing \"**{pushed_10}**\" out of Top 10'

		if pushed_25 := ctx_map.get(25) if placement <= 25 else None:
			if pushed_10:
				audit_description += f' and '
			else:
				audit_description += 'Pushing '

			audit_description += f'\"**{pushed_25}**\" out of Top 25'
		elif pushed_10 or pushed_25:
			audit_description += '!'

		await interaction.response.send_message(
			embed=embed(
				title=f'\"{name}\" by {publisher} placed at #{placement} on the Demonlist!',
				description=audit_description,
				footer=f'Level ID: {level_id}',
				color=Colour.green()
			)
		)

	@command(name='creator', description='Add a creator to the the Demonlist')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def creator(self, interaction: Interaction, level_id: LevelIDInt, creator: str) -> None:
		if not (result := await execute_get('SELECT name, publisher, creators FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, creators = result[0]
		creators = json.loads(creators)

		if creator.lower() in [c.lower() for c in creators]:
			return await interaction.response.send_message(embed=error_embed('This creator is already in the list!'), ephemeral=True)

		creators.append(creator)
		await execute_write('UPDATE demonlist SET creators = %s WHERE id = %s', (json.dumps(creators), level_id))
		await interaction.response.send_message(
			embed=success_embed(f'Added a new creator **{creator}** to \"**{name}**\" by {publisher}!')
		)

	@command(name='victor', description='Add a victor to the victors list')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def add_victor(self, interaction: Interaction, level_id: LevelIDInt, player_name: str, percentage: PercentageInt) -> None:
		if not (result := await execute_get('SELECT name, publisher, list_percentage, victors FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, list_percentage, victors = result[0]
		victors = json.loads(victors)

		if player_name.lower() in [value.get('name').lower() for value in victors]:
			return await interaction.response.send_message(embed=error_embed('This victor is already in the list!'), ephemeral=True)

		if percentage < list_percentage:
			return await interaction.response.send_message(embed=error_embed(f'The % cannot be less than the list %!'), ephemeral=True)

		victors.append({'name': player_name, '%': percentage})
		await execute_write('UPDATE demonlist SET victors = %s WHERE id = %s', (json.dumps(victors), level_id))
		await interaction.response.send_message(
			embed=success_embed(f'Added a new victor **{player_name}** (**{percentage}%**) to \"**{name}**\" by {publisher}!')
		)
