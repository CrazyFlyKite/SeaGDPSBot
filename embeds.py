from typing import Optional

from discord import Embed, Colour


def embed(title: Optional[str] = None, description: Optional[str] = None, footer: Optional[str] = None, color: Colour = Colour.blue()) -> Embed:
	embed_object: Embed = Embed(description=description, colour=color)

	if title:
		embed_object.title = title

	if footer:
		embed_object.set_footer(text=footer)

	return embed_object


def success_embed(description: str) -> Embed:
	return embed(description=description, color=Colour.green())


def error_embed(description: str) -> Embed:
	return embed(description=description, color=Colour.red())
