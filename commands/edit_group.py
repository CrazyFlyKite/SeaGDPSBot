from discord import Interaction
from discord.app_commands import command, guild_only, autocomplete, Group

from database import execute_get, execute_write
from decorators import log_command, limit_command, restrict_command, smart_describe
from embeds import success_embed, error_embed
from helpers import player_name_autocomplete, country_autocomplete
from utilities import *


class EditGroup(Group, name='edit'):
	@command(name='name', description='Edit a player\'s name')
	@guild_only()
	@limit_command
	@restrict_command()
	@autocomplete(name=player_name_autocomplete)
	@smart_describe()
	@log_command
	async def edit_name(self, interaction: Interaction, name: str, new_name: str) -> None:
		if not (player_data := await execute_get('SELECT player_id FROM players WHERE player_name = %s', (name,))):
			return await interaction.response.send_message(embed=error_embed(f'Player **{name}** not found!'), ephemeral=True)

		if (conflict := await execute_get('SELECT player_id FROM players WHERE LOWER(player_name) = LOWER(%s)', (new_name,))) and conflict[0][0] != player_data[0][0]:
			return await interaction.response.send_message(embed=error_embed(f'Player named **{new_name}** already exists!'), ephemeral=True)

		await execute_write('UPDATE players SET player_name = %s WHERE player_id = %s', (new_name, player_data[0][0]))
		await interaction.response.send_message(embed=success_embed(f'Renamed **{name}** to **{new_name}**!'))

	@command(name='nationality', description='Edit a player\'s nationality')
	@guild_only()
	@limit_command
	@restrict_command()
	@autocomplete(name=player_name_autocomplete, nationality=country_autocomplete)
	@smart_describe()
	@log_command
	async def edit_nationality(self, interaction: Interaction, name: str, nationality: str) -> None:
		if not (player_data := await execute_get('SELECT player_id FROM players WHERE player_name = %s', (name,))):
			return await interaction.response.send_message(embed=error_embed(f'Player **{name}** not found!'), ephemeral=True)

		countries: Dict[str, str] = {row[0]: row[1] for row in await execute_get('SELECT country_code, country_name FROM countries')}
		if nationality and nationality not in countries.keys():
			return await interaction.response.send_message(embed=error_embed('Select a country from the list!'), ephemeral=True)

		country_name: str = next((name for code, name in countries.items() if code == nationality), 'Unknown')
		await execute_write('UPDATE players SET nationality = %s WHERE player_id = %s', (nationality, player_data[0][0]))
		await interaction.response.send_message(embed=success_embed(f'The nationality of **{name}** changed to **{country_name}**!'))
