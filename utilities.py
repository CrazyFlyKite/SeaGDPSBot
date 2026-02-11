import json
import platform
from os import getenv
from typing import List, Dict, Any, Optional, Final, TypeAlias

from discord.app_commands import Choice, Range
from dotenv import load_dotenv

# Load the local environment
load_dotenv()

# Custom types
LevelIDInt: TypeAlias = Range[int, 1000]
PercentageInt: TypeAlias = Range[int, 1, 100]
PlacementInt: TypeAlias = Range[int, 1]

# Secrets
TOKEN: Final[Optional[str]] = getenv('TOKEN')
MYSQL_USER: Final[Optional[str]] = getenv('MYSQL_USER')
MYSQL_PASSWORD: Final[Optional[str]] = getenv('MYSQL_PASSWORD')

# Checking IP
IS_NAS: Final[bool] = platform.system() == 'Linux'
HOST_IP: Final[Optional[str]] = '172.17.0.1' if IS_NAS else getenv('SYNOLOGY_IP')

# Constants
with open('config/constants.json', 'r', encoding='utf-8') as file:
	config: Dict[str, Any] = json.load(file)

LOGGING_FORMAT: Final[str] = config.get('logging_format', None)
DATABASE: Final[str] = config.get('database', None)
DIFFICULTIES: Final[List[Choice]] = [Choice(name=name, value=value) for name, value in config.get('difficulties', {}).items()]
RATINGS: Final[List[Choice]] = [Choice(name=name, value=value) for name, value in config.get('ratings', {}).items()]
MODERATORS: Final[List[int]] = config.get('moderators', [])
DESCRIBED_PARAMETERS: Final[Dict[str, str]] = config.get('described_parameters', [])

with open('config/info_template.md', 'r', encoding='utf-8') as file:
	INFORMATION_MESSAGE: Final[str] = file.read()
