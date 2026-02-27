from discord import Interaction

from database import execute_get
from utilities import *


async def level_autocomplete(interaction: Interaction, current: str) -> List[Choice[int]]:
	return [
		Choice(name=player_name, value=level_id) for level_id, player_name in
		await execute_get('SELECT level_id, level_name FROM demonlist WHERE level_name LIKE %s ORDER BY placement LIMIT 25', (f'%{current}%',))
	]


async def player_name_autocomplete(interaction: Interaction, current: str) -> List[Choice[str]]:
	return [
		Choice(name=player_name, value=player_name) for (player_name,) in
		await execute_get('SELECT player_name FROM players WHERE player_name LIKE %s ORDER BY player_name LIMIT 25', (f'%{current}%',))
	]


async def country_autocomplete(interaction: Interaction, current: str) -> List[Choice[str]]:
	return [
		Choice(name=name, value=code)
		for name, code in COUNTRIES.items()
		if current.lower() in name.lower()
	][:25]
