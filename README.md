# SeaGDPSBot

### Requirements

![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue)

![discord](https://img.shields.io/badge/discord-2.3.2%2B-blue)
![mysql-connector-python](https://img.shields.io/badge/mysql-9.2.0%2B-red)
![python-dotenv](https://img.shields.io/badge/dotenv-1.0.0%2B-green)

## Introduction

**SeaGDPSBot** is a Discord bot for managing the official **SeaGDPS Demonlist**: **https://crazyflykite.com/seagdps/demonlist**

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


- [`comnands/add_group.py`](commands/add_group.py) - Commands for adding information to the database
- [`comnands/remove_group.py`](commands/remove_group.py) - Commands for removing information from the database
- [`comnands/move_group.py`](commands/move_group.py) - Commands for moving information in the database
- [`comnands/edit_group.py`](commands/edit_group.py) - Commands for editing information in the database

## Host

`docker-compose.yml` and `Dockerfile` are necessary, because the bot is hosted on my Synology NAS. `utilities.py` also has
platform detection functionality.

## .env

This project requires an `.env` file which looks like this:

```dotenv
TOKEN=???
MYSQL_USER=???
MYSQL_PASSWORD=???
SYNOLOGY_IP=???.???.?.??
```

## Contact

- **[My Website](https://crazyflykite.com)**
- **[Discord](https://discord.com/users/873920068571000833)**
- **[GitHub](https://github.com/CrazyFlyKite)**
- **[Email](mailto:karpenkoartem2846@gmail.com)**
