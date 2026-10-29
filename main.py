import logging
from datetime import datetime, timezone
from typing import Optional

from discord import Interaction, Intents, Game, Status, User, Forbidden
from discord.app_commands import guild_only, autocomplete, rename, AppCommandError, MissingRole, MissingAnyRole, \
	NoPrivateMessage
from discord.ext.commands import Bot
from discord.utils import escape_markdown

from audit_log import create_audit_task
from commands.edit_group import EditGroup
from database import execute_get, execute_write
from decorators import log_command, limit_command, restrict_command, smart_describe
from embeds import embed, success_embed, error_embed
from helpers import level_autocomplete, player_name_autocomplete, country_autocomplete, get_player_id, log_audit, \
	resolve_channel, is_valid_url, normalize_url
from setup_logging import setup_logging
from ui import SubmissionView
from utilities import *

# Setup logging
if IS_NAS:
	logging.basicConfig(level=logging.DEBUG, format=LOGGING_FORMAT)
else:
	setup_logging(level=logging.DEBUG, logging_format=LOGGING_FORMAT)

# Setup Bot
intents: Intents = Intents.default()
intents.message_content = True  # NOQA
bot: Bot = Bot(command_prefix='/', intents=intents, activity=Game(name='SeaGDPS'), status=Status.do_not_disturb)
audit_task = create_audit_task(bot)


# Startup
@bot.event
async def on_ready() -> None:
	logging.info(f'@{bot.user.name} is now running!')
	if not audit_task.is_running():
		audit_task.start()

	try:
		logging.info(f'Commands synced: {', '.join([command.name for command in await bot.tree.sync()])}')
	except Exception as exception:
		logging.error(f'Failed to sync commands: {exception}')


@bot.tree.error
async def on_app_command_error(interaction: Interaction, error: AppCommandError) -> None:
	if isinstance(error, (MissingRole, MissingAnyRole)):
		await interaction.response.send_message(embed=error_embed('You don\'t have the required role to use this command!'), ephemeral=True)
	elif isinstance(error, NoPrivateMessage):
		await interaction.response.send_message(embed=error_embed('You can\'t use this command in Direct Messages!'), ephemeral=True)
	else:
		logging.critical(f'Command Error: {error}')


# Commands
@bot.tree.command(name='info', description='Show information about the bot')
@log_command
async def info(interaction: Interaction) -> None:
	await interaction.response.send_message(embed=embed(description=INFORMATION_MESSAGE), ephemeral=True)


@bot.tree.command(name='submit', description='Submit a record')
@rename(level_id='level')
@autocomplete(level_id=level_autocomplete)
@smart_describe()
@log_command
async def submit(interaction: Interaction, level_id: str, completion_link: str, is_mobile: bool, percentage: Optional[PercentageInt] = None, time: Optional[str] = None) -> None:
	if not (player := await execute_get('SELECT player_id, player_name FROM players WHERE discord_id = %s', (interaction.user.id,))):
		return await interaction.response.send_message(embed=error_embed(f'You\'re not registered yet! Ask any mod to register you.'), ephemeral=True)

	player_id, player_name = player[0]

	# Get level
	level = await execute_get('''
	SELECT l.list_id, l.level_name, p.player_name, l.list_percentage, li.submissions_channel_id, li.record_mode, li.use_list_percentage
	FROM levels l
	JOIN lists li ON li.list_id = l.list_id
	LEFT JOIN creators c ON l.level_id = c.level_id AND c.is_publisher = 1
	LEFT JOIN players p ON c.player_id = p.player_id
	WHERE l.level_id = %s
	''', (level_id,))

	if not level:
		return await interaction.response.send_message(embed=error_embed('Level not found!'), ephemeral=True)

	list_id, level_name, publisher, list_percentage, submissions_channel_id, record_mode, use_list_percentage = level[0]
	submissions_channel = await resolve_channel(bot, submissions_channel_id)

	if submissions_channel is None:
		return await interaction.response.send_message(embed=error_embed('The submissions channel could not be found!'), ephemeral=True)

	# Data validation
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
	elif record_mode == 'time':
		if time is None:
			return await interaction.response.send_message(embed=error_embed('This list uses time records. Please, provide a completion time!'), ephemeral=True)

		if not TIME_REGEX.fullmatch(time):
			return await interaction.response.send_message(embed=error_embed('The time isn\'t in a correct format! Provide time in HH:MM:SS.mmm format.'), ephemeral=True)

	if not is_valid_url(completion_link):
		return await interaction.response.send_message(embed=error_embed('The proof is in incorrect format! **YouTube**, **Catbox** & **Medal** links only.'), ephemeral=True)

	completion_link = normalize_url(completion_link)

	# Get existing record, if exists
	existing_record = await execute_get('SELECT percentage FROM records WHERE level_id = %s AND player_id = %s', (level_id, player_id))

	if existing_record:
		existing_percentage = existing_record[0][0]
		if use_list_percentage:
			if int(percentage) < existing_percentage:
				return await interaction.response.send_message(embed=error_embed(f'The new % is lower than existing %!'), ephemeral=True)
		else:
			return await interaction.response.send_message(embed=error_embed(f'You already have a record on this level!'), ephemeral=True)

	# Message
	message: str = f'**{player_name}** submitted a record for "**{level_name}**" by {publisher}!'
	if percentage:
		message += f'\nProgress: **{percentage}%**'
	elif time:
		message += f'\nTime: **{time}**'
	message += f'\nProof: **{escape_markdown(completion_link)}**\nDevice: **{'Mobile :mobile_phone:' if is_mobile else 'PC :desktop:'}**\nStatus: **Pending** :alarm_clock:'

	try:
		await submissions_channel.send(embed=success_embed(message), view=SubmissionView(
			list_id=list_id,
			level_id=level_id,
			player_id=player_id,
			completion_link=completion_link,
			completion_time=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
			is_mobile=is_mobile,
			record_mode=record_mode,
			percentage=percentage,
			time=time
		))
	except Forbidden:
		return await interaction.response.send_message(embed=error_embed(f'Submission failed due to internal access issues.'), ephemeral=True)

	await interaction.response.send_message(embed=success_embed('Submitted!'), ephemeral=True)


@bot.tree.command(name='register', description='Register a new player')
@guild_only()
@limit_command
@restrict_command()
@autocomplete(nationality=country_autocomplete)
@smart_describe()
@log_command
async def register(interaction: Interaction, name: str, discord_profile: User, nationality: Optional[str] = None) -> None:
	if await execute_get('SELECT player_name FROM players WHERE LOWER(player_name) = LOWER(%s)', (name,)):
		return await interaction.response.send_message(embed=error_embed(f'Player **{name}** is already registered!'), ephemeral=True)

	countries: Dict[str, str] = {row[0]: row[1] for row in await execute_get('SELECT country_code, country_name FROM countries')}
	if nationality and nationality not in countries.keys():
		return await interaction.response.send_message(embed=error_embed('Select a country from the list!'), ephemeral=True)

	if str(discord_profile.id) in [row[0] for row in await execute_get('SELECT discord_id FROM players')]:
		return await interaction.response.send_message(embed=error_embed('This Discord profile already exists!'), ephemeral=True)

	await execute_write('INSERT INTO players (player_name, nationality, discord_id) VALUES (%s, %s, %s)', (name, nationality, str(discord_profile.id)))

	player_id: int = (await execute_get('SELECT player_id FROM players WHERE discord_id = %s', (str(discord_profile.id),)))[0][0]
	message: str = f'New player **{name}** registered! Welcome :3'
	await log_audit('add', 'player', None, await get_player_id(interaction.user), None, None, player_id, None, None, message)
	await interaction.response.send_message(embed=success_embed(message))


async def set_ban(interaction, name: str, banned: bool) -> None:
	if not (player_data := await execute_get('SELECT player_id, player_name, is_banned FROM players WHERE player_id = %s', (name,))):
		return await interaction.response.send_message(embed=error_embed(f'Player **{name}** not found!'), ephemeral=True)

	player_id, player_name, is_banned = player_data[0]
	action: str = 'banned' if banned else 'unbanned'

	if is_banned == banned:
		return await interaction.response.send_message(embed=error_embed(f'**{name}** is already {action}!'), ephemeral=True)

	await execute_write('UPDATE players SET is_banned = %s WHERE player_id = %s', (banned, player_id))

	message: str = f'**{player_name}** was {action}!'
	await log_audit('edit', 'player', 'is_banned', await get_player_id(interaction.user), None, None, player_id, not banned, banned, message)
	await interaction.response.send_message(embed=success_embed(message), ephemeral=True)


@bot.tree.command(name='ban', description='Ban a player')
@guild_only()
@limit_command
@restrict_command()
@autocomplete(name=player_name_autocomplete)
@smart_describe()
@log_command
async def ban(interaction, name: str) -> None:
	await set_ban(interaction, name, True)


@bot.tree.command(name='unban', description='Unban a player')
@guild_only()
@limit_command
@restrict_command()
@autocomplete(name=player_name_autocomplete)
@smart_describe()
@log_command
async def unban(interaction, name: str) -> None:
	await set_ban(interaction, name, False)


# Run
def main() -> None:
	bot.tree.add_command(EditGroup())
	bot.run(TOKEN)


if __name__ == '__main__':
	main()
