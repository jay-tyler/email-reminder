import twilio
from twilio.rest import TwilioRestClient


def send_sms(body, tonum, fromnum):
    account_sid = ""
    auth_token = ""
    client = TwilioRestClient(account_sid, auth_token)
    message = client.messages.create(body='{}'.format(body), to='{}'.format(tonum), from_='{}'.format(fromnum))
    print message.sid
    # try:
    #     client = twilio.rest.TwilioRestClient(account_sid, auth_token)
    #     message = client.messages.create(
    #         body="Hello World",
    #         to="+14159352345",
    #         from_="+14158141829"
    #     )
    # except twilio.TwilioRestException as e:
    #     print e

if __name__ == '__main__':
    send_sms('hellopea', 'tonumber', 'fromnumber')

