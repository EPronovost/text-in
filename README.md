# text-in
A Twilio Demo App for SMS Safety Checkins

---
Who texts anymore?  As communications move towards internet-based chats, one use case for SMS messaging remains:
communicating in limited cell coverage.  Often times, this communication is not to have lengthy conversations, 
but simply to "check-in" and confirm safety.

To this end, I wrote this demo app to implement a simple SMS-based safety network.

---
## Steps to Run

1. Add your Twilio credentials to [the keys file](src/keys.py).
2. Open two terminal windows for the directory.
3. In the first, run `source venv/bin/activate` to start the Twilio virtual machine
4. In the same window, run `./run-session` to start the session.  You can optionally pass in `--log LOG_FILE` to record
   the session.
5. Note what port your app is running on (will see something like 
    `* Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)`)
6. In the second window, start [ngrok](https://ngrok.com/) to tunnel to local host, using `./ngrok http PORT`
7. Note the forwarding URL, and copy it.
8. In your [Twilio Console](https://www.twilio.com/console/phone-numbers/incoming), set the messaging URL to the
    forwarding URL from above.

---
## How it Works

With the app live, a user texts the number.  They're then prompted to input a name to use, followed by how often
they want to check-in.

Once they've set up their profile, we start a new "check-in thread" for them that will periodically make sure they
text in, and escalate the situation if they don't.

Whenever a person texts in, their timer resets and their text is stored.  If the next deadline passes and the person
has not checked in, they are reminded.  If they still don't answer, an alert message is sent to all the contacts in
the chat.

### Design Considerations

The central idea of the project was a simple to use, lightweight tool to implement a safety net in a disparate group.
To avoid alarm fatigue, we keep notifications to a minimum.

### Threading

I wanted to explore the Python 
[`threading`](https://docs.python.org/2/library/threading.html#) library, so each user spawns a thread that performs
the periodic check-ins.  We also perform the full-group broadcasts on an asyncronous thread.

---
## Commands

The first three messages recieved are:
1. Initial registering of a phone number
2. The user's name
3. The check in frequency

After that, every message is regarded as a check-in.  There are several special commands.

* `@reset TIME`: reset the check-in interval for this user
* `@sos MESSAGE`: send an emergency alert to all users, forwarding the included message
* `@ok MESSAGE`: send an update to all users, saying you're ok
* `@stop`: stop check-ins
* `@quit`: leave the session (no longer receive broadcasts)

If a user stops, texting again will resume the check-ins.
