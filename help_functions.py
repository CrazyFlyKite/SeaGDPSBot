from discord import Interaction

from database import execute_get
from utilities import *


async def level_autocomplete(interaction: Interaction, current: str) -> List[Choice[int]]:
	return [
		Choice(name=name, value=level_id) for level_id, name in
		await execute_get('SELECT id, name FROM demonlist WHERE name LIKE %s ORDER BY placement', (f'%{current}%',))
	]
