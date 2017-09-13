
from person import *
from send_message import Messenger
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import time
import logging
import argparse
import threading

from keys import *

app = Flask(__name__)

contacts = {}

messenger = Messenger(ACCOUNT_SID, AUTH_TOKEN, TWILIO_NUMBER)

def broadcast(alert_message):
    for person in contacts.values():
        person.send_message(alert_message)
    log_message = '\n\t' + alert_message.replace('\n', '\n\t')
    logger.info('Broadcast to all: {}'.format(log_message))

def async_broadcast(alert_message):
    broadcast_thread = threading.Thread(target=broadcast, name='async_broadcast', args=(alert_message,))
    broadcast_thread.start()

@app.route('/', methods=['GET', 'POST'])
def handle_message():
    sender_number = request.values.get('From')
    body = request.values.get('Body', None).strip()

    if sender_number in contacts:
        try:
            reply_message = contacts[sender_number].handle_input(body, time.time())
        except UserQuit:
            del contacts[sender_number].check_in_thread
       		contacts[sender_number].active_lock.acquire()
        	contacts.pop(sender_number, None)
        	reply_message = 'Goodbye, and stay safe.'
    else:
        contacts[sender_number] = Person(sender_number, messenger, broadcast)
        reply_message = 'Welcome to Text-In! What is your name?'

    resp = MessagingResponse()
    if reply_message:
        resp.message(reply_message)
    return str(resp)

def parse_args():
    p = argparse.ArgumentParser('text-in')
    p.add_argument('--log', help='log file to use')

    return p.parse_args()

if __name__ == '__main__':
    args = parse_args()

    logger = logging.getLogger('text-in')
    logger.setLevel(logging.DEBUG)

    if args.log:
        ch = logging.FileHandler(args.log)
    else:
        ch = logging.StreamHandler()

    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s:\t%(message)s', '%m/%d/%Y %I:%M:%S %p')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info('Starting text-in session')
    app.run(debug=True)