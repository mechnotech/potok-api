import imaplib
import email
import base64
from datetime import datetime
from email.header import decode_header


class EmailAgent:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.mail = None
        self.indexes = None
        self.latest_code = None
        self.latest_code_time = None
        self.filter_from = '(FROM "noreply@potok.digital")'
        self.get_context()

    def get_context(self):
        self.mail = imaplib.IMAP4_SSL(self.config.mail_imap)
        self.mail.login(user=self.config.mail_login, password=self.config.mail_pass)
        self.mail.select("inbox")

    def __del__(self):
        self.close()

    def truncate_messages(self):
        status, messages = self.mail.search(None, "ALL")
        if status == 'OK' and messages[0]:
            indexes = [x for x in messages[0].split(b' ')]
        else:
            return
        for index in indexes:
            _, msg = self.mail.fetch(index, "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):

                        subject = subject.decode()
                    self.logger.debug(f'Deleting {subject}')
            self.mail.store(index, "+FLAGS", "\\Deleted")
        self.mail.expunge()
        self.logger.debug('Truncated messages OK')

    def get_latest_email_code(self):
        self.mail.check()

        status, data = self.mail.uid('search', None, self.filter_from)
        if status == 'OK' and data[0]:
            indexes = [int(x) for x in data[0].decode().split(' ')]
        else:
            return None, None
        indexes.sort(reverse=True)

        if indexes == self.indexes:
            return self.latest_code, self.latest_code_time

        self.indexes = indexes

        status, raw_email = self.mail.uid('fetch', str(self.indexes[0]), '(RFC822)')
        email_message = email.message_from_bytes(raw_email[0][1])

        final_message = ''
        for part in email_message.walk():
            if part.get_content_maintype() == 'text' and part.get_content_subtype() == 'plain':
                final_message = base64.b64decode(part.get_payload()).decode()

        final_message = final_message.split('Отписаться')[0]
        fm = final_message.split(' ')
        auth_code = fm[4]
        ts = datetime.strptime(f'{fm[5]} {fm[6]}', '%d.%m.%Y %H:%M')
        self.latest_code = auth_code
        self.latest_code_time = ts
        return auth_code, ts

    def close(self):
        pass
