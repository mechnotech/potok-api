import asyncpg


class DBPostgresRepository:

    def __init__(self, config):
        self.config = config
        self.dbapi_conn = None

    async def int_db(self):
        self.dbapi_conn = await asyncpg.create_pool(dsn=self.config.psg_connection_string)

    async def db_close_connection(self):
        await self.dbapi_conn.close()

    async def stage_croud_to_db(self, croud: list):
        async with self.dbapi_conn.acquire() as con:
            await con.copy_records_to_table(
                    table_name='croud_company',
                    schema_name='stage',
                    records=tuple(croud),
                    columns=('payload',)
            )
