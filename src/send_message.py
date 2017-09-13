
from twilio.rest import Client

class Messenger:
    def __init__(self, account_sid, auth_token, from_number):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number

    def dispatch_message(self, number, body):
        self.client.api.account.messages.create(
            from_=self.from_number,
            to=number,
            body=body
        )