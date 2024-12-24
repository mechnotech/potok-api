import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiohttp
from pydantic import BaseModel

from src.tools.mail_get import EmailAgent

base_dir = Path(__file__).parent.absolute()


class AuthTokens(BaseModel):
    token: str
    refresh_token: str
    ttl: datetime


class PotokApi:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.magent = EmailAgent(config, logger)
        self.user_company_id = self.config.user_company_id
        self.otp = None
        self.opt_wait_limit_seconds = 60
        self.token = None
        self.refresh_token = None
        self.token_ttl = None
        self.payload = {
            'login': self.config.api_login,
            'password': self.config.api_pass,
        }

    def get_headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    def is_token_outdated(self):
        return datetime.utcnow() >= self.token_ttl

    def load_token(self):
        try:
            with open(f'{base_dir}/auth/api_tokens.json', 'r') as f:
                tokens = json.load(f)
                self.token = tokens['token']
                self.refresh_token = tokens['refresh_token']
                self.token_ttl = datetime.fromtimestamp(tokens['ttl'])
        except FileNotFoundError:
            self.logger.warning('Cached tokens not found ...')

    def save_token(self):
        with open(f'{base_dir}/auth/api_tokens.json', 'w') as f:
            tokens = {'token': self.token, 'refresh_token': self.refresh_token, 'ttl': self.token_ttl.timestamp()}
            json.dump(tokens, f)
        self.logger.debug('Cached tokens set!')

    async def check_balance(self, user_company_id: str = None):
        """
        Вернуть баланс пользователя
        :param user_company_id:
        :return:
        """
        if self.is_token_outdated():
            await self.try_get_token()

        if not user_company_id:
            user_company_id = self.user_company_id

        url = f'https://i.potok.digital/api/companies/{user_company_id}/active-balance'

        async with aiohttp.ClientSession(headers=self.get_headers()) as session:
            result = await self.get_request(url=url, session=session)
        if result:
            return result

    async def get_croud_companies(self, user_company_id: str = None):
        """
        Вернуть список предложений для заема
        :param user_company_id:
        :return:
        """
        if self.is_token_outdated():
            await self.try_get_token()

        if not user_company_id:
            user_company_id = self.user_company_id

        url = f'https://i.potok.digital/api/projects/rising-funds?companyId={user_company_id}'

        try:
            async with aiohttp.ClientSession(headers=self.get_headers()) as session:
                result = await self.get_request(url=url, session=session)
            if result:
                return result
        except Exception as e:
            self.logger.error(e)

    def try_get_opt(self, limit: int = 6):
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

    async def get_request(self, url, session):
        async with session.get(url=url) as response:
            if response.status == 200:
                result = await response.json()
            else:
                text = await response.text()
                self.logger.error(f'Failed to get {url}: {response.status}, {text}')
                return
        return result

    def set_token(self, token_container):
        self.token = token_container.get('token')
        self.refresh_token = token_container.get('refreshToken')
        self.token_ttl = datetime.utcnow() + timedelta(hours=self.config.api_token_ttl)

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
            try:
                old_otp = self.payload.pop('otp', False)
                self.logger.debug(f'Old OTP extracted: {old_otp}' if old_otp else 'Try new OTP')
                next_stage_info = await self.post_request(f'{self.config.api_url}/users/login', self.payload, session)
                self.set_token(next_stage_info)
                if self.token:
                    return self.token
            except Exception as e:
                self.logger.warning(f'Token not found, try to get OTP! Status {e}')

    async def try_get_token(self):
        self.try_get_opt()

        if not self.otp:
            await self.request_otp()

        self.try_get_opt(self.opt_wait_limit_seconds)
        if not self.otp:
            exit('Cannot get OTP!')
        await self.get_token_with_otp()
        self.otp = None
        self.logger.debug(f'Token received: {self.token}, refresh token: {self.refresh_token}')
        self.save_token()

    async def run(self):
        self.load_token()

        balance = await self.check_balance(self.config.user_company_id)
        if balance:
            self.logger.info(f'API connected for user company {self.config.user_company_id}')
            return

        await self.try_get_token()
