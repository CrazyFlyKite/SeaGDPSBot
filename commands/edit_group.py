from discord import Interaction
from discord.app_commands import checks, choices, command, guild_only, autocomplete, rename, Group

from database import execute_get, execute_write
from decorators import log_command, limit_command, smart_describe
from embeds import success_embed, error_embed
from help_functions import level_autocomplete
from utilities import *


class EditGroup(Group, name='edit'):
	@command(name='name', description='Edit the name of a level')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def edit_name(self, interaction: Interaction, level_id: LevelIDInt, new_name: str) -> None:
		if not (result := await execute_get('SELECT name, publisher FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		old_name, publisher = result[0]

		if old_name == new_name:
			return await interaction.response.send_message(embed=error_embed('The new name is the same as the current name!'), ephemeral=True)

		await execute_write('UPDATE demonlist SET name = %s WHERE id = %s', (new_name, level_id))
		await interaction.response.send_message(embed=success_embed(f'\"**{old_name}**\" by {publisher} renamed to \"**{new_name}**\"!'))

	@command(name='publisher', description='Edit the publisher of a level')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def edit_publisher(self, interaction: Interaction, level_id: LevelIDInt, publisher: str) -> None:
		if not (result := await execute_get('SELECT name, publisher, creators FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, old_publisher, raw_creators = result[0]
		creators_list = json.loads(raw_creators)
		new_publisher: str = publisher.strip()
		match: str = next((c for c in creators_list if c.lower() == new_publisher.lower()), new_publisher)

		if old_publisher.lower() == new_publisher.lower() and creators_list[0] == old_publisher:
			return await interaction.response.send_message(embed=error_embed(f'**{match}** is already the publisher!'), ephemeral=True)

		creators_list = [creator for creator in creators_list if creator.lower() != new_publisher.lower()]
		creators_list.insert(0, match)

		await execute_write('UPDATE demonlist SET publisher = %s, creators = %s WHERE id = %s', (match, json.dumps(creators_list), level_id))
		await interaction.response.send_message(embed=success_embed(f'The publisher of \"**{name}**\" changed to **{match}**!'))

	@command(name='verifier', description='Edit the verifier of a level')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def edit_verifier(self, interaction: Interaction, level_id: LevelIDInt, new_verifier: str) -> None:
		if not (result := await execute_get('SELECT name, verifier, publisher FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, old_verifier, publisher = result[0]

		if old_verifier == new_verifier:
			return await interaction.response.send_message(embed=error_embed('The new verifier is the same as the current verifier!'), ephemeral=True)

		await execute_write('UPDATE demonlist SET verifier = %s WHERE id = %s', (new_verifier, level_id))
		await interaction.response.send_message(
			embed=success_embed(f'The verifier of \"**{name}**\" by {publisher} changed from **{old_verifier}** to **{new_verifier}**!')
		)

	@command(name='difficulty', description='Edit the difficulty of a level')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@choices(new_difficulty=DIFFICULTIES)
	@smart_describe()
	@log_command
	async def edit_difficulty(self, interaction: Interaction, level_id: LevelIDInt, new_difficulty: int) -> None:
		if not (result := await execute_get('SELECT name, publisher, difficulty FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, old_difficulty = result[0]

		if old_difficulty == new_difficulty:
			return await interaction.response.send_message(embed=error_embed('The new difficulty is the same as the current difficulty!'),
			                                               ephemeral=True)

		await execute_write('UPDATE demonlist SET difficulty = %s WHERE id = %s', (new_difficulty, level_id))
		await interaction.response.send_message(
			embed=success_embed(
				f'The difficulty of \"**{name}**\" by {publisher} changed from **{DIFFICULTIES[old_difficulty - 1].name}** to **{DIFFICULTIES[new_difficulty - 1].name}**!'
			)
		)

	@command(name='rating', description='Edit the rating of a level')
	@checks.has_any_role(*MODERATORS)
	@choices(new_rating=RATINGS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@choices(new_rating=RATINGS)
	@smart_describe()
	@log_command
	async def edit_rating(self, interaction: Interaction, level_id: LevelIDInt, new_rating: int) -> None:
		if not (result := await execute_get('SELECT name, publisher, rating FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, old_rating = result[0]

		if old_rating == new_rating:
			return await interaction.response.send_message(embed=error_embed('The new rating is the same as the current rating!'), ephemeral=True)

		await execute_write('UPDATE demonlist SET rating = %s WHERE id = %s', (new_rating, level_id))
		await interaction.response.send_message(
			embed=success_embed(
				f'The rating of \"**{name}**\" by {publisher} changed from **{RATINGS[old_rating - 1].name}** to **{RATINGS[new_rating - 1].name}**!'
			)
		)

	@command(name='list_percentage', description='Edit the list % of a level')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def edit_list_percentage(self, interaction: Interaction, level_id: LevelIDInt, new_list_percentage: PercentageInt) -> None:
		if not (result := await execute_get('SELECT name, publisher, list_percentage FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, old_list_percentage = result[0]

		if old_list_percentage == new_list_percentage:
			return await interaction.response.send_message(embed=error_embed('The new list % is the same as the current list %!'), ephemeral=True)

		await execute_write('UPDATE demonlist SET list_percentage = %s WHERE id = %s', (new_list_percentage, level_id))
		await interaction.response.send_message(
			embed=success_embed(f'The list % of \"**{name}**\" by {publisher} changed from **{old_list_percentage}%** to **{new_list_percentage}%**!')
		)

	@command(name='player', description='Edit a player\'s name across the Demonlist')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
	@limit_command
	@smart_describe()
	@log_command
	async def edit_player(self, interaction: Interaction, old_player_name: str, new_player_name: str) -> None:
		all_levels = await execute_get('SELECT id, publisher, creators, verifier, victors FROM demonlist')
		updated_count: int = 0

		for level_id, publisher, creators_json, verifier, victors_json in all_levels:
			changed = False

			if publisher == old_player_name:
				publisher = new_player_name
				changed = True

			if verifier == old_player_name:
				verifier = new_player_name
				changed = True

			creators = json.loads(creators_json)
			if old_player_name in creators:
				creators = [new_player_name if c == old_player_name else c for c in creators]
				changed = True

			victors: List[Dict[str, str | int]] = json.loads(victors_json)
			for victor in victors:
				if victor.get('name') == old_player_name:
					victor['name'] = new_player_name
					changed = True

			if changed:
				await execute_write('''
	            UPDATE demonlist
	            SET publisher = %s, creators = %s, verifier = %s, victors = %s
	            WHERE id = %s
	            ''', (publisher, json.dumps(creators), verifier, json.dumps(victors), level_id))
				updated_count += 1

		if updated_count > 0:
			await interaction.response.send_message(embed=success_embed(f'Renamed **{old_player_name}** to **{new_player_name}**!'))
		else:
			await interaction.response.send_message(
				embed=error_embed(f'Could not find any instances of **{old_player_name}**!'),
				ephemeral=True
			)

	@command(name='victor', description='Edit the % of a victor in the victors list')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@rename(level_id='id')
	@autocomplete(level_id=level_autocomplete)
	@smart_describe()
	@log_command
	async def edit_victor(self, interaction: Interaction, level_id: LevelIDInt, player_name: str, new_percentage: PercentageInt) -> None:
		if not (result := await execute_get('SELECT name, publisher, list_percentage, victors FROM demonlist WHERE id = %s', (level_id,))):
			return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

		name, publisher, list_percentage, victors = result[0]
		victors = json.loads(victors)

		if new_percentage < list_percentage:
			return await interaction.response.send_message(embed=error_embed(f'The % cannot be less than the list %!'), ephemeral=True)

		victor: Dict[str, str | int] = next((v for v in victors if v.get('name').lower() == player_name.lower()), None)

		if not victor:
			return await interaction.response.send_message(embed=error_embed('This victor is not in the list!'), ephemeral=True)

		victor['%'] = new_percentage
		await execute_write('UPDATE demonlist SET victors = %s WHERE id = %s', (json.dumps(victors), level_id))
		await interaction.response.send_message(
			embed=success_embed(f'The % of **{victor.get('name')}** changed to **{new_percentage}%** in \"**{name}**\" by {publisher}!')
		)
