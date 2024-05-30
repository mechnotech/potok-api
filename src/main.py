import asyncio
import logging

from src.settings import config
from tools.api import PotokApi

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger('Modem')

if __name__ == '__main__':
    api = PotokApi(config=config, logger=log)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(api.run())
