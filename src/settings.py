from pathlib import Path

from pydantic_settings import BaseSettings

base_dir = Path(__file__).parent.parent.absolute()

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 YaBrowser/23.5.1.750 Yowser/2.5 Safari/537.36'

class Settings(BaseSettings):
    dev_mode: bool = False
    log_level: str = 'DEBUG'

    api_url: str = 'https://i.potok.digital/api'
    api_login: str
    api_pass: str
    api_otp: str | None = None
    api_token: str | None = None
    api_token_ttl: int  # в часах

    app_message_creds: str
    app_chat_id: int
    app_chat_random_max_delay: int = 1


    mail_imap: str
    mail_login: str
    mail_pass: str

    user_company_id: str

    db_postgres_host: str
    db_postgres_port: int = 5432
    db_postgres_user: str
    db_postgres_pass: str
    db_postgres_name: str
    db_postgres_schema: str

    @property
    def psg_connection_string(self) -> str:
        return (
            'postgresql://{}:{}@{}:{}/{}'.format(
                self.db_postgres_user,
                self.db_postgres_pass,
                self.db_postgres_host,
                self.db_postgres_port,
                self.db_postgres_name,

            )
        )

    def apsg_connection_string(self) -> str:
        return (
            'postgresql+asyncpg://{}:{}@{}:{}/{}'.format(
                self.db_postgres_user,
                self.db_postgres_pass,
                self.db_postgres_host,
                self.db_postgres_port,
                self.db_postgres_name,

            )
        )

    class Config:
        env_file = f'{base_dir}/.env'


config = Settings()
