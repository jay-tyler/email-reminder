import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage
import pytest
import email
import imaplib
from email_sender_gmail import send
from email_receiver_gmail import receive
from mock import patch
import unittest
from email_sender_gmail import send
from email_receiver_gmail import get_email, process_email, receive
import send_sms
import twilio
from twilio.rest import TwilioRestClient


# if the selected mailbox does not exist, "select" will return this:
#     ('NO', ['[NONEXISTENT] Unknown Mailbox: baloons (now in authenticated state) (Failure)'])

def test_send_email():
    with patch('smtplib.SMTP') as mock_smtp:
        fromaddr = 'scatterpeas@gmail.com'
        toaddrs = 'scatterpeas@gmail.com'
        subject = 'Greeting'
        text = "This is text \n Hi!\nHow are you?\nI'm a scattered pea.\nhttps://www.youtube.com/watch?v=jHm0jmg-sbc"
        send(fromaddr, toaddrs, subject, text)
        instance = mock_smtp.return_value
        for method_name in ['starttls', 'login', 'sendmail', 'quit']:
            method = getattr(instance, method_name)
            assert method.called is True
            assert method.call_count == 1


def test_get_emaiil():
    expected = 'MIME-Version: 1.0\r\nReceived: by 10.36.1.73 with HTTP; Tue, 14 Jul 2015 16:27:50 -0700 (PDT)\r\nDate: Tue, 14 Jul 2015 16:27:50 -0700\r\nDelivered-To: scatterpeas@gmail.com\r\nMessage-ID: <CAJVJxF1WiQOsMevi7QDcCO+qxuf4G5P05t60CheqeB_1dsqdmA@mail.gmail.com>\r\nSubject: cronjob\r\nFrom: Pea Body <scatterpeas@gmail.com>\r\nTo: Pea Body <scatterpeas@gmail.com>\r\nContent-Type: multipart/alternative; boundary=bcaec5489fb7d14ca2051ade2fbb\r\n\r\n--bcaec5489fb7d14ca2051ade2fbb\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n*/2 * * * * /Library/Frameworks/Python.framework/Versions/2.7/bin/python\r\n/Users/sakiukaji/Projects/feature_email/email_sender_gmail.py\r\n\r\n--bcaec5489fb7d14ca2051ade2fbb\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n<div dir="ltr">\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n<p class=""><span class="">*/2 * * * * /Library/Frameworks/Python.framework/Versions/2.7/bin/python /Users/sakiukaji/Projects/feature_email/email_sender_gmail.py</span></p></div>\r\n\r\n--bcaec5489fb7d14ca2051ade2fbb--'
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        imap_client = mock_imap.return_value
        imap_client.select.return_value = ('OK', ['36'])
        imap_client.search.return_value = ('OK', ['2 3 5 8 17 18 19 20 21 22'])
        imap_client.fetch.return_value = ('OK', [('22 (RFC822 {958}', expected), ' FLAGS (\\Seen))'])

        raw_email = get_email()
        assert raw_email == expected







# def test_send_sms():
#     with patch(TwilioRestClient(account_sid, auth_token))as mock_sms:
#         # fromnum = '+16319564194'
#         # tonum = '+12069542208'
#         # message = client.messages.create(body='hellopea', to='+12069542208', from_='+16319564194')
#         # send_sms(body, tonum, fromnum)
#         send_sms('hellopea', '+12069542208', '+16319564194', 'https://theinfinitevariety.files.wordpress.com/2010/11/47nakedmolerat.jpg')
#         instance = mock_sms.return_value
#         assert instance.sendmail.called is True
#         assert instance.sendmail.call_count == 1


