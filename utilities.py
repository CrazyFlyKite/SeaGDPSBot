import json
from os import getenv
from re import compile, Pattern
from typing import List, Dict, Any, Final, TypeAlias

from discord.app_commands import Range
from dotenv import load_dotenv

# Custom types
PercentageInt: TypeAlias = Range[int, 1, 100]

# Secrets
def require_env(name: str) -> str:
	if not (value := getenv(name)):
		raise RuntimeError(f'Missing env variable: {name}')

	return value


load_dotenv()
TOKEN: Final[str] = require_env('TOKEN')
MYSQL_USER: Final[str] = require_env('MYSQL_USER')
MYSQL_PASSWORD: Final[str] = require_env('MYSQL_PASSWORD')

# Checking IP
IS_NAS: Final[bool] = require_env('ENV') == 'LIVE'
HOST_IP: Final[str] = '172.17.0.1' if IS_NAS else require_env('SERVER_IP')

# Constants
with open('config/constants.json', 'r', encoding='utf-8') as file:
	config: Dict[str, Any] = json.load(file)

LOGGING_FORMAT: Final[str] = config.get('logging_format', '')
DATABASE: Final[str] = config.get('database', '')
DEVELOPER_ID: Final[int] = config.get('developer_id', 0)
DESCRIBED_PARAMETERS: Final[Dict[str, str]] = config.get('described_parameters', [])
URL_REGEXES: Final[List[Pattern]] = [compile(pattern) for pattern in config.get('url_regexes', [])]
TIME_REGEX: Final[Pattern] = config.get('time_regex', '')

with open('config/info_template.md', 'r', encoding='utf-8') as file:
	INFORMATION_MESSAGE: Final[str] = file.read().rstrip()
