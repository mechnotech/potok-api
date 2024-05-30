import time
from datetime import datetime, timedelta

import aiohttp

from src.tools.mail_get import EmailAgent


class PotokApi:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.magent = EmailAgent(config, logger)
        self.otp = None
        self.opt_wait_limit_seconds = 60
        self.token = None
        self.refresh_token = None
        self.token_ttl = None
        self.payload = {
            'login': self.config.api_login,
            'password': self.config.api_pass,
        }
        self.try_get_opt()

    def try_get_opt(self, limit: int = 4):
        if self.otp:
            return
        for i in range(limit):
            otp, ts = self.magent.get_latest_email_code()
            if otp:
                self.logger.info(f'OPT received: {otp}')
                self.otp = otp
                self.magent.truncate_messages()
                return
            time.sleep(1)
            self.logger.debug(f'Waiting for OPT... {i}. Old OTP: {self.otp}')

    async def post_request(self, url, data, session):
        async with session.post(url=url, data=data) as response:
            if response.status == 200:
                result = await response.json()
            else:
                text = await response.text()
                self.logger.error(f'Failed to get {url}: {response.status}, {text}')
                raise Exception(response.status)
        return result

    def set_token(self, token_container):
        self.token = token_container.get('token')
        self.refresh_token = token_container.get('refreshToken')
        self.token_ttl = datetime.now() + timedelta(hours=24)

    async def get_token_with_otp(self):
        async with aiohttp.ClientSession() as session:
            self.payload['otp'] = self.otp
            final_stage_info = await self.post_request(f'{self.config.api_url}/users/otp', self.payload, session)
            if final_stage_info.get('error'):
                self.logger.error(f'Failed to get token: {final_stage_info.get("error")}')
                return
            if final_stage_info.get('isSuccessful'):
                self.set_token(final_stage_info)

    async def request_otp(self):
        async with aiohttp.ClientSession() as session:
            next_stage_info = await self.post_request(f'{self.config.api_url}/users/login', self.payload, session)
            self.set_token(next_stage_info)
            if self.token:
                return self.token
            self.logger.warning('Token not found, try to get OTP!')

    async def run(self):
        if not self.otp:
            await self.request_otp()

        self.try_get_opt(self.opt_wait_limit_seconds)
        if not self.otp:
            exit('Cannot get OTP!')
        await self.get_token_with_otp()
        self.otp = None
        self.logger.info(f'Token received: {self.token}, refresh token: {self.refresh_token}')
