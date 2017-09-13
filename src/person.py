'''
The object for a Person.
'''

# Wait 3 minutes after requesting a checkin
CHECK_IN_WAIT_TIME = 1

import time
import threading
import logging

HELP_MESSAGE = '@sos MSG: send an emergency message to all\n' \
               '@ok MSG: send an ok message to all\n' \
               '@reset TIME: reset check-in interval\n' \
               '@stop: stop check-ins\n' \
               '@quit: quit the service (no longer receive updates)'

check_in_to_minutes_ago = lambda t: int((time.time() - t) / 60)

logger = logging.getLogger('text-in')

class UserQuit(SystemExit):
    pass

class Person:
    def __init__(self, number, messenger, broadcast_all):
        # The number is a unique identifier
        self.number = number

        # The messenger object to use to communicate
        self.messenger = messenger

        # Method to broadcast a message to the entire group
        self.broadcast_all = broadcast_all

        # The waiter thread to check on this Person
        self.check_in_thread = None
        self.active_lock = threading.Lock()
        self.is_active = True

        # Will be instantiated later
        self.name = None

        self.time_interval = None
        self.next_check_in = None
        self.last_check_in_message = None
        self.last_check_in_time = None

        self.waiting = False

    def __eq__(self, other):
        return isinstance(other, Person) and self.number == other.number

    def __repr__(self):
        return '{} ({})'.format(self.name, self.number) if self.name else self.number

    def send_message(self, text):
        self.messenger.dispatch_message(self.number, text)

    def handle_input(self, text, time):
        if self.name is None:
            return self.__set_name(text)
        elif self.time_interval is None:
            return self.__set_time_interval(text)
        else:
            return self.__handle_check_in(text, time)

    def __set_name(self, text):
        if (self.name is not None):
            return

        if len(text) == 0:
            self.send_message('Please input a valid name.')
            return

        self.name = text
        logger.info('New user {} ({})'.format(self.name, self.number))
        return 'Welcome {}!\nHow often would you like to check-in? Please enter an integer in minutes.'.format(text)

    def __set_time_interval(self, text):
        try:
            value = int(text)
            if value <= 0:
                raise ValueError
            self.time_interval = value
            self.last_check_in_time = time.time()
            self.last_check_in_message = text
            self.next_check_in = time.time() + 60 * self.time_interval

            self.check_in_thread = threading.Thread(target=self.timer_update, name='{}_check_in'.format(self.name))
            self.check_in_thread.start()
            logger.debug('{} updated check-in interval to {} min'.format(self.name, self.time_interval))
            return 'Next check-in in {} mins.'.format(self.time_interval)

        except ValueError:
            return 'Unable to parse time "{}". Please input an integer.'.format(text)

    def __handle_check_in(self, text, time):
        if len(text) > 0 and text[0] == '@':
            if not self.is_active:
                self.active_lock.release()
                self.is_active = True
            return self.__handle_command(text, time)

        self.last_check_in_time = time
        self.last_check_in_message = text
        self.next_check_in = time + 60 * self.time_interval
        self.waiting = False
        logger.info('{} check-in: "{}"'.format(self.name, text))

        if not self.is_active:
            self.active_lock.release()
            self.is_active = True
        return 'Check-in recieved.  Next check-in in {} minutes.'.format(self.time_interval)

    def __handle_command(self, text, time):
        index = text.find(' ')
        if index == -1:
            command = text
            body = ''
        else:
            command, body = text[:index], text[index + 1:]

        command = command.lower()

        if command == '@sos':
            logger.warning('@sos from {}: "{}"'.format(self.name, body))
            alert_message = 'ALERT: {} send an @sos\n{}\n"{}"'.format(self.name, self.number, body)
            self.broadcast_all(alert_message)
            return
        elif command == '@reset':
            return self.__set_time_interval(body.strip())
        elif command == '@stop':
            if self.is_active:
                self.active_lock.acquire()
                self.is_active = False
            logger.info('{} stopped check-ins'.format(self.name))
            return 'Stopped check-ins. Text again to resume.'
        elif command == '@ok':
            logger.info('{} is ok: "{}"'.format(self.name, body))
            alert_message = 'UPDATE: {} is @ok\n"{}"'.format(self.name, body)
            self.broadcast_all(alert_message)
            return self.__handle_check_in(body, time)
        elif command == '@quit':
            logger.info('{} quit the session'.format(self.name))
            raise UserQuit
        else:
            return 'Unknown command "{}"\n{}'.format(command, HELP_MESSAGE)

    def timer_update(self):
        while True:
            self.active_lock.acquire()
            current_time = time.time()

            if current_time < self.next_check_in:
                sleep_time = self.next_check_in - current_time
            elif not self.waiting:
                self.waiting = True
                self.send_message('Please check-in. The timer is up.')
                logger.info('Notifying {} to check in'.format(self.name))
                sleep_time = 60 * CHECK_IN_WAIT_TIME
            else:
                logger.warning('{} failed to check-in'.format(self.name))
                alert_message = 'ALERT: {} failed to check-in\n{}\nLast check-in {} minutes ago:\n"{}"'.format(
                    self.name,
                    self.number,
                    check_in_to_minutes_ago(self.last_check_in_time),
                    self.last_check_in_message
                )
                self.broadcast_all(alert_message)
                self.send_message('Alert sent. Text "@ok MSG" to send an ok message to the group.')
                sleep_time = 2 * 60 * CHECK_IN_WAIT_TIME

            self.active_lock.release()
            time.sleep(sleep_time)
