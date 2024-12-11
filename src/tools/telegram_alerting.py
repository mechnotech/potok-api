import asyncio
import random
from logging import Logger

import aiohttp
from pydantic_settings import BaseSettings


class BaseAlerting:

    def __init__(self, config: BaseSettings, logger: Logger):
        self.config = config
        self.logger = logger
        self.url = None

    async def send(self, message) -> None:
        raise NotImplementedError

    async def warning(self, error: BaseException, **kwargs) -> None:
        raise NotImplementedError

    async def error(self, error: BaseException, **kwargs) -> None:
        raise NotImplementedError


class TelegramAlerting(BaseAlerting):

    def __init__(self, config: BaseSettings, logger: Logger):
        super().__init__(config, logger)
        self.logger = logger
        self.api_key = config.app_message_creds
        self.chat_id = config.app_chat_id
        self.max_delay = config.app_chat_random_max_delay
        self.url = f'https://api.telegram.org/bot{self.api_key}/sendMessage'
        self.send_file_url = f'https://api.telegram.org/bot{self.api_key}/sendDocument'
        self.dummy_send = False

    async def send_report(self, message: str):
        try:
            with open(self.config.report_path, 'rb') as f:
                data = {'chat_id': self.chat_id, 'caption': message, 'document': f}

                async with aiohttp.ClientSession() as session:
                    async with session.post(url=self.send_file_url, data=data) as r:
                        if r.status != 200:
                            self.logger.warning(f'TG-bot message not delivered - status {r.status}')

        except Exception as e:
            self.logger.warning(f'TG-bot connection error - {e}')

    async def send(self, message: str):
        if self.dummy_send:
            self.logger.warning('Dummy Telegram send: {}'.format(message))
            return
        params = {'chat_id': self.chat_id, 'text': message}
        if self.max_delay:
            await asyncio.sleep(random.uniform(0, self.max_delay))
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=self.url, params=params) as r:
                    if r.status != 200:
                        self.logger.warning(f'TG-bot message not delivered - status {r.status}')
        except Exception as e:
            self.logger.warning(f'TG-bot connection error - {e}')

    async def warning(self, error: BaseException, **kwargs) -> None:
        message = f'⚠️ Остановлен скрипт Potok API 🛠️'
        await self.send(message)

    async def error(self, error: BaseException, **kwargs) -> None:
        message = f'🔥 Ошибка  Potok API. {type(error)}. {str(error)}'
        await self.send(message)


class DummyAlerting(TelegramAlerting):

    async def send(self, message: str):
        self.logger.info(f'TELEGRAM BOT: Dummy sending message: {message}')

    async def send_report(self, message: str):
        self.logger.info(f'TELEGRAM BOT: Dummy sent report ... ')
