from typing import Tuple, Optional

from discord import Interaction, Colour
from discord.app_commands import choices, command, guild_only, autocomplete, rename, Group
from mysql.connector import DataError

from database import execute_get, execute_write
from decorators import log_command, limit_command, restrict_command, smart_describe
from embeds import embed, success_embed, error_embed
from help_functions import list_name_autocomplete, level_autocomplete, player_name_autocomplete, country_autocomplete
from utilities import *


class AddGroup(Group, name='add'):
	@command(name='level', description='Add a level to the list')
	@guild_only()
	@limit_command
	@restrict_command(arg='list_id', is_list_id=True)
	@rename(list_id='list', level_id='id')
	@autocomplete(list_id=list_name_autocomplete, publisher=player_name_autocomplete, verifier=player_name_autocomplete)
	@choices(difficulty=DIFFICULTIES, rating=RATINGS)
	@smart_describe()
	@log_command
	async def add_level(self, interaction: Interaction, list_id: int, placement: PlacementInt, level_id: LevelIDInt, name: str, publisher: str, verifier: str,
	                    difficulty: Optional[int] = None, rating: Optional[int] = None, list_percentage: Optional[PercentageInt] = None) -> None:
		if not (result := await execute_get('SELECT record_mode, use_list_percentage, use_difficulty FROM lists WHERE list_id = %s', (list_id,))):
			return await interaction.response.send_message(embed=error_embed(f'This list doesn\'t exist!'), ephemeral=True)

		record_mode, use_list_percentage, use_difficulty = result[0]

		if await execute_get('SELECT level_name FROM levels WHERE level_id = %s', (level_id,)):
			return await interaction.response.send_message(embed=error_embed(f'Level with ID **{level_id}** already exists!'), ephemeral=True)

		list_context: List[Tuple[int, str]] = await execute_get('SELECT placement, level_name FROM levels WHERE list_id = %s AND placement IN (10, 25)', (list_id,))
		ctx_map: Dict[int, str] = {row[0]: row[1] for row in list_context}
		publisher_data: List[str] = await execute_get('SELECT player_id FROM players WHERE player_name = %s', (publisher,))
		verifier_data: List[str] = await execute_get('SELECT player_id FROM players WHERE player_name = %s', (verifier,))

		if not publisher_data:
			return await interaction.response.send_message(embed=error_embed(f'The publisher isn\'t registered yet! Use `/add player` first.'), ephemeral=True)

		if not verifier_data:
			return await interaction.response.send_message(embed=error_embed(f'The verifier isn\'t registered yet! Use `/add player` first.'), ephemeral=True)

		max_placement: int = (await execute_get('SELECT MAX(placement) FROM levels WHERE list_id = %s', (list_id,)))[0][0] + 1

		if not (1 <= placement <= max_placement):
			return await interaction.response.send_message(embed=error_embed(f'The placement be between **1** and **{max_placement}**!'), ephemeral=True)

		if use_difficulty and (difficulty is None or rating is None):
			return await interaction.response.send_message(embed=error_embed(f'This list requires difficulty and ratings!'), ephemeral=True)

		if use_list_percentage and list_percentage is None:
			return await interaction.response.send_message(embed=error_embed(f'This list requires list %!'), ephemeral=True)

		await execute_write('UPDATE levels SET placement = placement + 1 WHERE list_id = %s AND placement >= %s ORDER BY placement DESC', (list_id, placement))
		await execute_write(
			'INSERT INTO levels (level_id, list_id, placement, level_name, difficulty, rating, list_percentage) VALUES (%s, %s, %s, %s, %s, %s, %s)',
			(level_id, list_id, placement, name, difficulty, rating, list_percentage if use_list_percentage else None)
		)
		await execute_write('INSERT INTO creators (level_id, player_id, is_publisher) VALUES (%s, %s, TRUE)', (level_id, publisher_data[0][0]))
		await execute_write('INSERT INTO records (level_id, player_id, percentage, is_verifier) VALUES (%s, %s, %s, TRUE)', (level_id, verifier_data[0][0], None if record_mode == 'time' else 100))

		audit_description: str = ''

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
				title=f'\"{name}\" by {publisher} placed at #{placement} on the list!',
				description=audit_description,
				footer=f'Level ID: {level_id}',
				color=Colour.green()
			)
		)

	@command(name='creator', description='Add a creator to a level')
	@guild_only()
	@limit_command
	@restrict_command(arg='level_id')
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete, creator=player_name_autocomplete)
	@smart_describe()
	@log_command
	async def add_creator(self, interaction: Interaction, level_id: LevelIDInt, creator: str) -> None:
		result = await execute_get('''
        SELECT l.level_name, p.player_name
        FROM levels l
        LEFT JOIN creators c ON l.level_id = c.level_id AND c.is_publisher = TRUE
        LEFT JOIN players p ON c.player_id = p.player_id
        WHERE l.level_id = %s
	    ''', (level_id,))

		if not result:
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		level_name, publisher = result[0]

		if not (player_data := await execute_get('SELECT player_id, player_name FROM players WHERE player_name = %s', (creator,))):
			return await interaction.response.send_message(embed=error_embed(f'Player **{creator}** is not registered yet! Use `/add player` first.'), ephemeral=True)

		player_id, player_name = player_data[0]

		if existing := await execute_get('SELECT is_publisher FROM creators WHERE level_id = %s AND player_id = %s', (level_id, player_id)):
			return await interaction.response.send_message(embed=error_embed(f'**{player_name}** is {'the publisher' if existing[0][0] else 'already a creator'} of this level!'), ephemeral=True)

		await execute_write('INSERT INTO creators (level_id, player_id, is_publisher) VALUES (%s, %s, 0)', (level_id, player_id))
		await interaction.response.send_message(embed=success_embed(f'Added **{player_name}** as a creator of \"**{level_name}**\" by {publisher}!'))

	@command(name='victor', description='Add/Update a victor to/of a level')
	@guild_only()
	@limit_command
	@restrict_command(arg='level_id')
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete, player_name=player_name_autocomplete)
	@smart_describe()
	@log_command
	async def add_victor(self, interaction: Interaction, level_id: LevelIDInt, player_name: str, percentage: Optional[PercentageInt] = None, time: Optional[str] = None) -> None:
		result = await execute_get('''
		SELECT l.level_name, p.player_name, l.list_percentage, li.record_mode, li.use_list_percentage
        FROM levels l
        JOIN lists li ON li.list_id = l.list_id
        LEFT JOIN creators c ON l.level_id = c.level_id AND c.is_publisher = TRUE
        LEFT JOIN players p ON c.player_id = p.player_id
        WHERE l.level_id = %s
        ''', (level_id,))

		if not result:
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		level_name, publisher, list_percentage, record_mode, use_list_percentage = result[0]

		if (percentage is None) == (time is None):
			return await interaction.response.send_message(embed=error_embed('Either % or time must be filled, not both or none!'), ephemeral=True)

		if record_mode == 'percentage':
			if percentage is None:
				return await interaction.response.send_message(embed=error_embed('This list uses % records. Please, provide %!'), ephemeral=True)

			if use_list_percentage:
				if percentage < list_percentage:
					return await interaction.response.send_message(embed=error_embed(f'The % cannot be less than the list % (**{list_percentage}%**)!'), ephemeral=True)
			else:
				if percentage < 100:
					return await interaction.response.send_message(embed=error_embed('This list requires 100% completions!'), ephemeral=True)

		if not (player_data := await execute_get('SELECT player_id FROM players WHERE player_name = %s', (player_name,))):
			return await interaction.response.send_message(embed=error_embed(f'Player **{player_name}** is not registered yet! Use `/add player` first :)'), ephemeral=True)

		record_status = await execute_get('SELECT is_verifier FROM records WHERE level_id = %s AND player_id = %s', (level_id, player_data[0][0]))

		if record_status and record_status[0][0] == 1:
			return await interaction.response.send_message(embed=error_embed(f'**{player_name}** is the verifier of this level!'), ephemeral=True)

		progress: str = f'{percentage}%'
		if record_mode == 'percentage':
			await execute_write('''
			INSERT INTO records (level_id, player_id, percentage)
			VALUES (%s, %s, %s)
			ON DUPLICATE KEY UPDATE
			percentage = %s
			''', (level_id, player_data[0][0], percentage, percentage))
		elif record_mode == 'time':
			try:
				progress: str = str(time)
				await execute_write('''
				INSERT INTO records (level_id, player_id, time_spent)
				VALUES (%s, %s, %s)
				ON DUPLICATE KEY UPDATE time_spent = %s
				''', (level_id, player_data[0][0], time, time))
			except DataError:
				return await interaction.response.send_message(embed=error_embed(f'The time is in incorrect format!'), ephemeral=True)

		await interaction.response.send_message(embed=success_embed(f'Added/Updated record for **{player_name}** (**{progress}**) on \"**{level_name}**\" by {publisher}!'))

	@command(name='player', description='Register a new player to the database')
	@guild_only()
	@limit_command
	@restrict_command(arg='level_id')
	@autocomplete(player_nationality=country_autocomplete)
	@smart_describe()
	@log_command
	async def add_player(self, interaction: Interaction, player_name: str, player_nationality: Optional[str] = None) -> None:
		if await execute_get('SELECT player_name FROM players WHERE LOWER(player_name) = LOWER(%s)', (player_name,)):
			return await interaction.response.send_message(embed=error_embed(f'Player **{player_name}** is already registered!'), ephemeral=True)

		if player_nationality and player_nationality not in COUNTRIES.values():
			return await interaction.response.send_message(embed=error_embed('Select a country from the list!'), ephemeral=True)

		await execute_write('INSERT INTO players (player_name, player_nationality) VALUES (%s, %s)', (player_name, player_nationality))
		await interaction.response.send_message(embed=success_embed(f'New player **{player_name}** registered!'))
