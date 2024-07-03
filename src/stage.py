import asyncio
import json
import logging
import re

from src.settings import config
from src.tools.repositories.db_postgres import DBPostgresRepository
from src.tools.api import PotokApi

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger('Modem')
pattern = re.compile('.[^A-Z]*')


def to_snake(pascal: str) -> str:
    """Converts a Pascal case string to snake case.
    """
    magic = re.findall(pattern, pascal)
    snake = '_'.join(magic)
    snake = snake.lower()

    return snake


def croud_parser(croud):
    new_croud = dict()

    for key, value in croud.items():
        new_croud[to_snake(key)] = value
    return new_croud


async def start_pipline():
    loans_ids = set()
    borrowers_ids = set()
    api = PotokApi(config=config, logger=log)
    db = DBPostgresRepository(config=config)
    await db.int_db()
    await api.run()

    try:
        while True:
            loans_candidates = await api.get_croud_companies()
            to_stage = []
            if not loans_candidates:
                balance = await api.check_balance()
                if not balance:
                    await asyncio.sleep(160)
                    log.warning('Try reconnect and receive new tokens. Wait a minute ...')
                    await api.try_get_token()
                    continue

            for candidate in loans_candidates:
                loans_ids.add(candidate['id'])
                borrowers_ids.add(candidate['borrower']['id'])
                to_stage.append((json.dumps(candidate, ensure_ascii=False),))
            await db.stage_croud_to_db(to_stage)
            log.info(f'Staged {len(loans_ids)} loans to db, unique borrowers: {len(borrowers_ids)}, loans {len(loans_ids)}')
            await asyncio.sleep(60*10)
    finally:
        await db.db_close_connection()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_pipline())
