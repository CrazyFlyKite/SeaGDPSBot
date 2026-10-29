import logging
from typing import Optional

from discord import AllowedMentions, Colour, Forbidden, NotFound
from discord.ext import tasks
from discord.utils import escape_markdown

from database import execute_get, execute_write
from embeds import embed
from helpers import resolve_channel


async def post_pending(bot) -> None:
	rows = await execute_get('''
        SELECT a.audit_id, a.source, a.message, p.player_name, li.audit_channel_id, a.list_id
        FROM audit_log a
        LEFT JOIN players p ON p.player_id = a.actor_player_id
        LEFT JOIN levels l ON l.level_id = a.level_id
        LEFT JOIN lists li ON li.list_id = a.list_id
        WHERE a.notified = 0 AND a.notify = 1
        ORDER BY a.audit_id
        LIMIT 50
    ''')

	for audit_id, source, message, actor, raw_channel_id, list_id in rows:
		if message:
			try:
				if list_id is None:
					channel_row = await execute_get('SELECT audit_channel_id FROM lists WHERE list_id = 1')
					raw_channel_id = channel_row[0][0] if channel_row else None

				channel = await resolve_channel(bot, raw_channel_id)

				if channel is None:
					logging.warning(f'Audit #{audit_id} has no channel (its list has no audit_channel_id), skipped')
				else:
					await channel.send(
						embed=embed(description=f'{message}\n-# *\\- {escape_markdown(actor or 'Unknown')}*', color=Colour.green()),
						allowed_mentions=AllowedMentions.none()
					)
			except (Forbidden, NotFound, ValueError):
				logging.error(f'Audit #{audit_id}: channel {raw_channel_id} is unavailable, skipped')

		await execute_write('UPDATE audit_log SET notified = 1 WHERE audit_id = %s', (audit_id,))


def create_audit_task(bot):
	@tasks.loop(seconds=10)
	async def audit_task() -> None:
		try:
			await post_pending(bot)
		except Exception as exception:
			logging.error(f'Audit log poll failed: {exception}')

	@audit_task.before_loop
	async def before_audit_task() -> None:
		await bot.wait_until_ready()

	return audit_task
