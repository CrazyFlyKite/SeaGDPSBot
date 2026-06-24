# SeaGDPSBot

### Requirements

![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue)

![discord](https://img.shields.io/badge/discord-2.3.2%2B-blue)
![mysql-connector-python](https://img.shields.io/badge/mysql--connector--python-9.7.0%2B-red)
![python-dotenv](https://img.shields.io/badge/python--dotenv-1.2.1%2B-green)

## Introduction

**SeaGDPSBot** is a Discord bot for managing the official **SeaGDPS Demonlist**: **https://crazyflykite.com/seagdps**

- Detailed command documentation can be found in [`config/info_template.md`](config/info_template.md)
- Version changelog can be found in [`CHANGELOG.md`](CHANGELOG.md)
- Bot configurations can be found in [`config/constants.json`](config/constants.json)

## File Structure

- [`main.py`](main.py) - Main entry point
- [`decorators.py`](decorators.py) - Custom wrapper functions for commands
- [`database.py`](database.py) - Functions for database interactions
- [`embeds.py`](embeds.py) - Custom embed templates for Discord messages
- [`help_functions.py`](help_functions.py) - Custom functions for commands
- [`utilities.py`](utilities.py) - Constants and platform detection
- [`setup_logging.py`](setup_logging.py) - Enhanced terminal logging


- [`commands/add_group.py`](commands/add_group.py) - Commands for adding information to the database
- [`commands/remove_group.py`](commands/remove_group.py) - Commands for removing information from the database
- [`commands/move_group.py`](commands/move_group.py) - Commands for moving information in the database
- [`commands/edit_group.py`](commands/edit_group.py) - Commands for editing information in the database
- [`commands/set_group.py`](commands/set_group.py) - Commands for adding, removing and editing information in the database all at the same time

## Host

[`docker-compose.yml`](docker-compose.yml) and [`Dockerfile`](Dockerfile) are necessary, because the bot is hosted on my Synology NAS.
[`utilities.py`](utilities.py) also has platform detection functionality.

## .env

This project requires an `.env` file which looks like this:

```dotenv
ENV=DEV/LIVE
LIVE_TOKEN=???
DEV_TOKEN=???

THUMBNAILS_PATH=/???/???/???/???/

MYSQL_USER=???
MYSQL_PASSWORD=???

SERVER_IP=???.???.???.???
```

## Contact

- **[My Website](https://crazyflykite.com)**
- **[Discord](https://discord.com/users/873920068571000833)**
- **[GitHub](https://github.com/CrazyFlyKite)**
- **[Email](mailto:karpenkoartem2846@gmail.com)**
