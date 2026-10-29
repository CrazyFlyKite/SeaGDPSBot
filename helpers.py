from typing import Optional
from urllib.parse import urlparse, parse_qs, ParseResult

from discord import Interaction, User
from discord.app_commands import Choice
from discord.utils import escape_markdown

from database import execute_get, execute_write
from utilities import *


async def level_autocomplete(interaction: Interaction, current: str) -> List[Choice]:
	choices = []

	for level_id, level_name in await execute_get('SELECT level_id, level_name FROM levels WHERE level_name LIKE %s ORDER BY level_name LIMIT 25', (f'{current}%',)):
		if not level_name:
			continue

		choices.append(Choice(name=str(level_name)[:100], value=str(level_id)))

	return choices


async def player_name_autocomplete(interaction: Interaction, current: str) -> List[Choice]:
	return [
		Choice(name=player_name[:100], value=str(player_id)) for (player_name, player_id) in
		await execute_get('SELECT player_name, player_id FROM players WHERE player_name LIKE %s ORDER BY player_name LIMIT 25', (f'%{current}%',))
	]


async def list_name_autocomplete(interaction: Interaction, current: str) -> List[Choice]:
	return [
		Choice(name=display_name[:100], value=list_id) for list_id, display_name in
		await execute_get('SELECT list_id, display_name FROM lists WHERE display_name LIKE %s ORDER BY list_id LIMIT 25', (f'%{current}%',))
	]


async def country_autocomplete(interaction: Interaction, current: str) -> List[Choice]:
	return [
		Choice(name=name, value=code)
		for code, name in {row[0]: row[1] for row in await execute_get('SELECT country_code, country_name FROM countries ORDER BY country_name LIMIT 25')}.items()
		if current.lower() in name.lower()
	][:25]


def is_valid_url(url: str) -> bool:
	return any(regex.fullmatch(url) for regex in URL_REGEXES)


def normalize_url(url: str) -> str:
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


async def get_player_name(user: User) -> str:
	return escape_markdown((await execute_get('SELECT player_name FROM players WHERE discord_id = %s', (user.id,)))[0][0])


async def get_player_id(user: User) -> int:
	return (await execute_get('SELECT player_id FROM players WHERE discord_id = %s', (user.id,)))[0][0]


async def resolve_channel(bot, raw_channel_id: Optional[str]):
	if not raw_channel_id:
		return None

	return bot.get_channel(int(raw_channel_id)) or await bot.fetch_channel(int(raw_channel_id))


async def log_audit(action: str, entity: str, field: str, actor_player_id: int, list_id: int, level_id: int, player_id: int, old_value: Any, new_value: Any, message: str) -> None:
	await execute_write(
		'INSERT INTO audit_log (action, entity, field, source, actor_player_id, list_id, level_id, player_id, old_value, new_value, message, notified) VALUES (%s, %s, %s, \'bot\', %s, %s, %s, %s, %s, %s, %s, 1)',
		(action, entity, field, actor_player_id, list_id, level_id, player_id, old_value, new_value, message)
	)
