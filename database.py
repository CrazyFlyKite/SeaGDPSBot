from typing import Tuple

import mysql.connector

from utilities import *


async def execute_get(code: str, parameters: Optional[Tuple[Any, ...]] = None) -> List[Any]:
	connection = mysql.connector.connect(host=HOST_IP, user=MYSQL_USER, passwd=MYSQL_PASSWORD, database=DATABASE)
	cursor = connection.cursor()

	try:
		cursor.execute(code, parameters)
		return cursor.fetchall()
	finally:
		cursor.close()
		connection.close()


async def execute_write(code: str, parameters: Optional[Tuple[Any, ...]] = None) -> None:
	connection = mysql.connector.connect(host=HOST_IP, user=MYSQL_USER, passwd=MYSQL_PASSWORD, database=DATABASE)
	cursor = connection.cursor()

	try:
		cursor.execute(code, parameters)
		connection.commit()
	finally:
		cursor.close()
		connection.close()
