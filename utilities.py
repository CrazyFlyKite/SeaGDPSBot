import json
import platform
from os import getenv
from typing import List, Dict, Any, Final, TypeAlias, Tuple

from discord.app_commands import Choice, Range
from dotenv import load_dotenv

# Load the local environment
load_dotenv()

# Custom types
LevelIDInt: TypeAlias = Range[int, 1000]
PercentageInt: TypeAlias = Range[int, 1, 100]
PlacementInt: TypeAlias = Range[int, 1]


# Secrets
def require_env(name: str) -> str:
	if not (value := getenv(name)):
		raise RuntimeError(f'Missing env variable: {name}')

	return value


TOKEN: Final[str] = require_env('LIVE_TOKEN') if getenv('ENV') == 'LIVE' else require_env('DEV_TOKEN')
MYSQL_USER: Final[str] = require_env('MYSQL_USER')
MYSQL_PASSWORD: Final[str] = require_env('MYSQL_PASSWORD')
THUMBNAILS_PATH: Final[str] = require_env('THUMBNAILS_PATH')

# Checking IP
IS_NAS: Final[bool] = platform.system() == 'Linux'
HOST_IP: Final[str] = '172.17.0.1' if IS_NAS else require_env('SERVER_IP')

# Constants
with open('config/constants.json', 'r', encoding='utf-8') as file:
	config: Dict[str, Any] = json.load(file)

LOGGING_FORMAT: Final[str] = config.get('logging_format', '')
DATABASE: Final[str] = config.get('database', '')
DEVELOPER_ID: Final[int] = config.get('developer_id', 0)
DIFFICULTIES: Final[List[Choice]] = [Choice(name=name, value=value) for name, value in config.get('difficulties', {}).items()]
RATINGS: Final[List[Choice]] = [Choice(name=name, value=value) for name, value in config.get('ratings', {}).items()]
DESCRIBED_PARAMETERS: Final[Dict[str, str]] = config.get('described_parameters', [])
ALLOWED_EXTENSIONS: Final[Tuple[str, ...]] = tuple(config.get('allowed_image_formats', {}).get('allowed_extension', []))
ALLOWED_TYPES: Final[Tuple[str, ...]] = tuple(config.get('allowed_image_formats', {}).get('allowed_types', []))

with open('config/info_template.md', 'r', encoding='utf-8') as file:
	INFORMATION_MESSAGE: Final[str] = file.read()

with open('config/countries.json', 'r', encoding='utf-8') as file:
	COUNTRIES: Final[Dict[str, str]] = json.load(file)
