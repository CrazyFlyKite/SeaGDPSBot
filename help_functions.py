from urllib.parse import urlparse, parse_qs, ParseResult

from discord import Interaction

from database import execute_get
from utilities import *


async def level_autocomplete(interaction: Interaction, current: str) -> List[Choice]:
	choices = []

	for level_id, level_name in await execute_get('SELECT level_id, level_name FROM levels WHERE level_name LIKE %s ORDER BY level_name LIMIT 25', (f'{current}%',)):
		if not level_name:
			continue

		choices.append(Choice(name=str(level_name)[:100], value=level_id))

	return choices


async def player_name_autocomplete(interaction: Interaction, current: str) -> List[Choice]:
	return [
		Choice(name=player_name, value=player_name) for (player_name,) in
		await execute_get('SELECT player_name FROM players WHERE player_name LIKE %s ORDER BY player_name LIMIT 25', (f'%{current}%',))
	]


async def list_name_autocomplete(interaction: Interaction, current: str) -> List[Choice]:
	return [
		Choice(name=display_name, value=list_id) for list_id, display_name in
		await execute_get('SELECT list_id, display_name FROM lists WHERE display_name LIKE %s ORDER BY list_id LIMIT 25', (f'%{current}%',))
	]


async def country_autocomplete(interaction: Interaction, current: str) -> List[Choice]:
	return [
		Choice(name=name, value=code)
		for name, code in COUNTRIES.items()
		if current.lower() in name.lower()
	][:25]


def normalize_showcase_url(url: str) -> str:
	parsed: ParseResult = urlparse(url)

	if parsed.netloc in {'www.youtube.com', 'youtube.com', 'm.youtube.com'} and parsed.path == '/watch':
		query: Dict[str, List[str]] = parse_qs(parsed.query)
		video_id: str = query.get('v', [None])[0]

		if video_id:
			result = f'https://youtu.be/{video_id}'

			if 't' in query:
				result += f'?t={query['t'][0]}'

			return result

	if parsed.netloc == 'youtu.be':
		video_id = parsed.path.lstrip('/').split('/')[0]
		result = f'https://youtu.be/{video_id}'

		query = parse_qs(parsed.query)

		if 't' in query:
			result += f'?t={query['t'][0]}'

		return result

	return url
