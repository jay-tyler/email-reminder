import twilio
from twilio.rest import TwilioRestClient


def send_sms(body, tonum, fromnum, media_url=None):
    account_sid = ""
    auth_token = ""
    try:
        client = TwilioRestClient(account_sid, auth_token)
        message = client.messages.create(body='{}'.format(body), to='{}'.format(tonum), from_='{}'.format(fromnum), media_url='{}'.format(media_url))
        print message.sid
    except twilio.TwilioRestException as e:
        print e


def receive_sms():
    client = TwilioRestClient(account_sid, auth_token)
    for message in client.messages.list():
        print message.body


if __name__ == '__main__':
    send_sms('hellopea', '+12069542208', '+16319564194', 'https://theinfinitevariety.files.wordpress.com/2010/11/47nakedmolerat.jpg')
    # receive_sms()
