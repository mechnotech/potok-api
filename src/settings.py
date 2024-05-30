from pathlib import Path

from pydantic_settings import BaseSettings

base_dir = Path(__file__).parent.parent.absolute()

USER_AGENT = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 YaBrowser/23.5.1.750 Yowser/2.5 Safari/537.36')

class Settings(BaseSettings):
    dev_mode: bool = False
    log_level: str = 'DEBUG'

    api_url: str = 'https://i.potok.digital/api'
    api_login: str
    api_pass: str
    api_otp: str | None = None
    api_token: str | None = None

    mail_imap: str
    mail_login: str
    mail_pass: str

    class Config:
        env_file = f'{base_dir}/.env'


config = Settings()
