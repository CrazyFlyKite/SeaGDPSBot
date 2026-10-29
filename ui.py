from discord import Interaction, ButtonStyle
from discord.ui import button, View, Button

from database import execute_get, execute_write
from embeds import error_embed
from helpers import get_player_name, log_audit
from utilities import DEVELOPER_ID


async def is_list_mod(interaction: Interaction, list_id: int) -> bool:
	if not interaction.guild:
		return False

	if interaction.user.id == DEVELOPER_ID:
		return True

	if (member := interaction.guild.get_member(interaction.user.id)) is None:
		member = await interaction.guild.fetch_member(interaction.user.id)

	return bool({row[0] for row in await execute_get('SELECT moderator_role_id FROM lists WHERE list_id = %s', (list_id,))} & {str(role.id) for role in member.roles})


class SubmissionView(View):
	def __init__(self, list_id: int, level_id: int, player_id: int, completion_link: str, completion_time: str, is_mobile: bool, record_mode: str, percentage: int, time: str) -> None:
		super().__init__(timeout=None)
		self.list_id = list_id
		self.level_id = level_id
		self.player_id = player_id
		self.completion_link = completion_link
		self.completion_time = completion_time
		self.is_mobile = is_mobile
		self.record_mode = record_mode
		self.percentage = percentage
		self.time = time
		self.decided = False

	async def interaction_check(self, interaction: Interaction) -> bool:
		if self.decided:
			await interaction.response.send_message(embed=error_embed('This submission has already been reviewed!'), ephemeral=True)
			return False

		if not await is_list_mod(interaction, self.list_id):
			await interaction.response.send_message(embed=error_embed('You are not a moderator of this list!'), ephemeral=True)
			return False

		if str(interaction.user.id) == (await execute_get('SELECT discord_id FROM players WHERE player_id = %s', (self.player_id,)))[0][0]:
			await interaction.response.send_message(embed=error_embed('You cannot review your own submission!'), ephemeral=True)
			return False

		return True

	async def process(self, interaction: Interaction, action_button: Button, accept: bool) -> None:
		self.decided = True

		for item in self.children:
			item.disabled = True

		if accept:
			if self.record_mode == 'percentage':
				await execute_write('''
					INSERT INTO records (level_id, player_id, completion, completion_time, percentage, is_mobile)
					VALUES (%s, %s, %s, %s, %s, %s)
					ON DUPLICATE KEY UPDATE percentage = %s
					''', (self.level_id, self.player_id, self.completion_link, self.completion_time, self.percentage, self.is_mobile, self.percentage))
			elif self.record_mode == 'time':
				await execute_write('''
					INSERT INTO records (level_id, player_id, completion, completion_time, time_spent, is_mobile)
					VALUES (%s, %s, %s, %s, %s, %s)
					ON DUPLICATE KEY UPDATE time_spent = %s
					''', (self.level_id, self.player_id, self.completion_link, self.completion_time, self.time, self.is_mobile, self.time))

		embed = interaction.message.embeds[0]
		embed.description = embed.description.replace(
			'Status: **Pending** :alarm_clock:',
			f'Status: **{'Accepted :white_check_mark:' if accept else 'Rejected :x:'}** *(by {await get_player_name(interaction.user)})*'
		)

		if accept:
			await log_audit('edit', 'record', None, interaction.user.id, self.list_id, self.level_id, self.player_id, None, None, embed.description)

		await interaction.response.edit_message(embed=embed, view=self)

	@button(label='Accept', style=ButtonStyle.success, custom_id='submission:accept')
	async def accept(self, interaction: Interaction, accept_button: Button) -> None:
		await self.process(interaction, accept_button, True)

	@button(label='Reject', style=ButtonStyle.danger, custom_id='submission:reject')
	async def reject(self, interaction: Interaction, reject_button: Button) -> None:
		await self.process(interaction, reject_button, False)
