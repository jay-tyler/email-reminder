import twilio
from twilio.rest import TwilioRestClient
import os

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, 'twilio_creds.txt'), 'r') as fh:
    account_sid = fh.readline().strip()
    auth_token = fh.readline().strip()


def send_sms(body, tonum, fromnum, media_url=None):
    try:
        client = TwilioRestClient(account_sid, auth_token)
        message = client.messages.create(body='{}'.format(body), to='{}'.format(tonum), from_='{}'.format(fromnum), media_url=media_url)
        print message.sid
    except twilio.TwilioRestException as e:
        print e
        raise ValueError(e)


def receive_sms():
    client = TwilioRestClient(account_sid, auth_token)
    for message in client.messages.list():
        print message.body


if __name__ == '__main__':
    send_sms('hellopea', '+14258943425', '+16319564194', 'https://theinfinitevariety.files.wordpress.com/2010/11/47nakedmolerat.jpg')
    # receive_sms()
