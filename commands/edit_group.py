from discord import Interaction
from discord.app_commands import choices, command, guild_only, autocomplete, rename, Group

from database import execute_get, execute_write
from decorators import log_command, limit_command, restrict_command, smart_describe
from embeds import success_embed, error_embed
from help_functions import level_autocomplete, player_name_autocomplete, country_autocomplete
from utilities import *


class EditGroup(Group, name='edit'):
	@command(name='name', description='Edit the name of a level')
	@guild_only()
	@limit_command
	@restrict_command(level_id_arg='level_id')
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def edit_name(self, interaction: Interaction, level_id: LevelIDInt, new_name: str) -> None:
		result = await execute_get('''
		SELECT l.level_name, p.player_name
        FROM levels l
        LEFT JOIN creators c ON l.level_id = c.level_id AND c.is_publisher = TRUE
        LEFT JOIN players p ON c.player_id = p.player_id
        WHERE l.level_id = %s
        ''', (level_id,))

		if not result:
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		old_name, publisher = result[0]

		if old_name == new_name:
			return await interaction.response.send_message(embed=error_embed('The new name is the same as the current name!'), ephemeral=True)

		await execute_write('UPDATE levels SET level_name = %s WHERE level_id = %s', (new_name, level_id))
		await interaction.response.send_message(embed=success_embed(f'\"**{old_name}**\" by {publisher} renamed to \"**{new_name}**\"!'))

	@command(name='publisher', description='Edit the publisher of a level')
	@guild_only()
	@limit_command
	@restrict_command(level_id_arg='level_id')
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete, publisher=player_name_autocomplete)
	@smart_describe()
	@log_command
	async def edit_publisher(self, interaction: Interaction, level_id: LevelIDInt, publisher: str) -> None:
		if not (level_data := await execute_get('SELECT level_name FROM levels WHERE level_id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		level_name = level_data[0][0]

		if not (player_data := await execute_get('SELECT player_id, player_name FROM players WHERE player_name = %s', (publisher,))):
			return await interaction.response.send_message(embed=error_embed(f'Player **{publisher}** is not registered!'), ephemeral=True)

		player_id, player_name = player_data[0]
		current_publisher = await execute_get('SELECT player_id FROM creators WHERE level_id = %s AND is_publisher = TRUE', (level_id,))

		if current_publisher and current_publisher[0][0] == player_id:
			return await interaction.response.send_message(embed=error_embed(f'**{player_name}** is already the publisher!'), ephemeral=True)

		await execute_write('UPDATE creators SET is_publisher = FALSE WHERE level_id = %s AND is_publisher = TRUE', (level_id,))
		await execute_write('INSERT INTO creators (level_id, player_id, is_publisher) VALUES (%s, %s, TRUE) ON DUPLICATE KEY UPDATE is_publisher = TRUE', (level_id, player_id))

		await interaction.response.send_message(embed=success_embed(f'The publisher of \"**{level_name}**\" changed to **{player_name}**!'))

	@command(name='verifier', description='Edit the verifier of a level')
	@guild_only()
	@limit_command
	@restrict_command(level_id_arg='level_id')
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete, new_verifier=player_name_autocomplete)
	@smart_describe()
	@log_command
	async def edit_verifier(self, interaction: Interaction, level_id: LevelIDInt, new_verifier: str) -> None:
		level_data = await execute_get('''
        SELECT l.level_name, p.player_name
        FROM levels l
        LEFT JOIN creators c ON l.level_id = c.level_id AND c.is_publisher = TRUE
        LEFT JOIN players p ON c.player_id = p.player_id
        WHERE l.level_id = %s
	    ''', (level_id,))

		if not level_data:
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		level_name, publisher = level_data[0]

		old_verifier_data = await execute_get('''
        SELECT p.player_name, p.player_id
        FROM records r
        JOIN players p ON r.player_id = p.player_id
        WHERE r.level_id = %s AND r.is_verifier = TRUE
	    ''', (level_id,))

		old_verifier_name: str = old_verifier_data[0][0]

		if old_verifier_name == new_verifier:
			return await interaction.response.send_message(embed=error_embed('The new verifier is the same as the current verifier!'), ephemeral=True)

		if not (new_player_data := await execute_get('SELECT player_id FROM players WHERE player_name = %s', (new_verifier,))):
			return await interaction.response.send_message(embed=error_embed(f'Player **{new_verifier}** is not registered yet! Use `/add player` first.'), ephemeral=True)

		await execute_write('UPDATE records SET is_verifier = FALSE WHERE level_id = %s AND is_verifier = TRUE', (level_id,))
		await execute_write('''
        INSERT INTO records (level_id, player_id, progress, is_verifier)
        VALUES (%s, %s, 100, 1)
        ON DUPLICATE KEY UPDATE is_verifier = TRUE, progress = 100
	    ''', (level_id, new_player_data[0][0]))

		await interaction.response.send_message(embed=success_embed(f'The verifier of \"**{level_name}**\" by {publisher} changed from **{old_verifier_name}** to **{new_verifier}**!'))

	@command(name='difficulty', description='Edit the difficulty of a level')
	@guild_only()
	@limit_command
	@restrict_command(level_id_arg='level_id')
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@choices(new_difficulty=DIFFICULTIES)
	@smart_describe()
	@log_command
	async def edit_difficulty(self, interaction: Interaction, level_id: LevelIDInt, new_difficulty: int) -> None:
		result = await execute_get('''
		SELECT l.level_name, p.player_name, l.difficulty
        FROM levels l
        LEFT JOIN creators c ON l.level_id = c.level_id AND c.is_publisher = TRUE
        LEFT JOIN players p ON c.player_id = p.player_id
        WHERE l.level_id = %s
        ''', (level_id,))

		if not result:
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, old_difficulty = result[0]

		if old_difficulty == new_difficulty:
			return await interaction.response.send_message(embed=error_embed('The new difficulty is the same as the current difficulty!'), ephemeral=True)

		await execute_write('UPDATE levels SET difficulty = %s WHERE level_id = %s', (new_difficulty, level_id))
		await interaction.response.send_message(
			embed=success_embed(f'The difficulty of \"**{name}**\" by {publisher} changed from **{DIFFICULTIES[old_difficulty - 1].name}** to **{DIFFICULTIES[new_difficulty - 1].name}**!')
		)

	@command(name='rating', description='Edit the rating of a level')
	@guild_only()
	@limit_command
	@restrict_command(level_id_arg='level_id')
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@choices(new_rating=RATINGS)
	@smart_describe()
	@log_command
	async def edit_rating(self, interaction: Interaction, level_id: LevelIDInt, new_rating: int) -> None:
		result = await execute_get('''
		SELECT l.level_name, p.player_name, l.rating
        FROM levels l
        LEFT JOIN creators c ON l.level_id = c.level_id AND c.is_publisher = TRUE
        LEFT JOIN players p ON c.player_id = p.player_id
        WHERE l.level_id = %s
        ''', (level_id,))

		if not result:
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, old_rating = result[0]

		if old_rating == new_rating:
			return await interaction.response.send_message(embed=error_embed('The new rating is the same as the current rating!'), ephemeral=True)

		await execute_write('UPDATE levels SET rating = %s WHERE level_id = %s', (new_rating, level_id))
		await interaction.response.send_message(
			embed=success_embed(f'The rating of \"**{name}**\" by {publisher} changed from **{RATINGS[old_rating - 1].name}** to **{RATINGS[new_rating - 1].name}**!')
		)

	@command(name='list_percentage', description='Edit the list % of a level')
	@guild_only()
	@limit_command
	@restrict_command(level_id_arg='level_id')
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def edit_list_percentage(self, interaction: Interaction, level_id: LevelIDInt, new_list_percentage: PercentageInt) -> None:
		result = await execute_get('''
		SELECT l.level_name, p.player_name, l.list_percentage, li.use_list_percentage
        FROM levels l
        JOIN lists li ON l.list_id = li.list_id
        LEFT JOIN creators c ON l.level_id = c.level_id AND c.is_publisher = TRUE
        LEFT JOIN players p ON c.player_id = p.player_id
        WHERE l.level_id = %s
        ''', (level_id,))

		if not result:
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, old_list_percentage, use_list_percentage = result[0]

		if not use_list_percentage:
			return await interaction.response.send_message(embed=error_embed('This list doesn\'t use list %!'), ephemeral=True)

		if old_list_percentage == new_list_percentage:
			return await interaction.response.send_message(embed=error_embed('The new list % is the same as the current list %!'), ephemeral=True)

		await execute_write('UPDATE levels SET list_percentage = %s WHERE level_id = %s', (new_list_percentage, level_id))
		await interaction.response.send_message(embed=success_embed(f'The list % of \"**{name}**\" by {publisher} changed from **{old_list_percentage}%** to **{new_list_percentage}%**!'))

	@command(name='player_name', description='Edit a player\'s name')
	@guild_only()
	@limit_command
	@restrict_command(level_id_arg='level_id')
	@autocomplete(old_player_name=player_name_autocomplete)
	@smart_describe()
	@log_command
	async def edit_player_name(self, interaction: Interaction, old_player_name: str, new_player_name: str) -> None:
		if not (player_data := await execute_get('SELECT player_id FROM players WHERE player_name = %s', (old_player_name,))):
			return await interaction.response.send_message(embed=error_embed(f'Player **{old_player_name}** not found!'), ephemeral=True)

		if (conflict := await execute_get('SELECT player_id FROM players WHERE LOWER(player_name) = LOWER(%s)', (new_player_name,))) and conflict[0][0] != player_data[0][0]:
			return await interaction.response.send_message(embed=error_embed(f'Player named **{new_player_name}** already exists!'), ephemeral=True)

		await execute_write('UPDATE players SET player_name = %s WHERE player_id = %s', (new_player_name, player_data[0][0]))
		await interaction.response.send_message(embed=success_embed(f'Renamed **{old_player_name}** to **{new_player_name}**!'))

	@command(name='player_nationality', description='Edit a player\'s nationality')
	@guild_only()
	@limit_command
	@restrict_command(level_id_arg='level_id')
	@autocomplete(player_name=player_name_autocomplete, player_nationality=country_autocomplete)
	@smart_describe()
	@log_command
	async def edit_player_nationality(self, interaction: Interaction, player_name: str, player_nationality: str) -> None:
		if not (player_data := await execute_get('SELECT player_id FROM players WHERE player_name = %s', (player_name,))):
			return await interaction.response.send_message(embed=error_embed(f'Player **{player_name}** not found!'), ephemeral=True)

		if player_nationality and player_nationality not in COUNTRIES.values():
			return await interaction.response.send_message(embed=error_embed('Select a country from the list!'), ephemeral=True)

		country_name: str = next((name for name, code in COUNTRIES.items() if code == player_nationality), 'Unknown')

		await execute_write('UPDATE players SET nationality = %s WHERE player_id = %s', (player_nationality, player_data[0][0]))
		await interaction.response.send_message(embed=success_embed(f'The nationality of **{player_name}** changed to **{country_name}**!'))
