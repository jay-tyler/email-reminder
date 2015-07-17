import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage
import pytest
import email
import imaplib
from email_sender_gmail import send
from email_receiver_gmail import receive
from mock import patch,call, Mock
import unittest
from email_sender_gmail import send
from email_receiver_gmail import get_email, process_email, receive
from send_sms import send_sms
import twilio
from twilio.rest import TwilioRestClient
import urllib2


# if the selected mailbox does not exist, "select" will return this:
#     ('NO', ['[NONEXISTENT] Unknown Mailbox: baloons (now in authenticated state) (Failure)'])

def test_send_email():
    with patch('smtplib.SMTP') as mock_smtp:
        fromaddr = 'scatterpeas@gmail.com'
        toaddrs = 'scatterpeas@gmail.com'
        subject = 'Greeting'
        text = "This is text \n Hi!\nHow are you?\nI'm a scattered pea.\nhttps://www.youtube.com/watch?v=jHm0jmg-sbc"
        html = """
               <html>
                 <head></head>
                 <body>
                   <p>Hi!<br>
                       This is HTML<br>
                       How are you?<br>
                       I'm a scattered pea. <a href="https://www.youtube.com/watch?v=jHm0jmg-sbc">Watch this</a>
                   </p>
                 </body>
               </html>
                """
        attachment = 'nmr.jpg'
        send(fromaddr, toaddrs, subject, text, html, attachment)
        instance = mock_smtp.return_value
        for method_name in ['starttls', 'login', 'sendmail', 'quit']:
            method = getattr(instance, method_name)
            assert method.called is True
            assert method.call_count == 1


def test_get_email():
    expected = 'MIME-Version: 1.0\r\nReceived: by 10.36.1.73 with HTTP; Tue, 14 Jul 2015 16:27:50 -0700 (PDT)\r\nDate: Tue, 14 Jul 2015 16:27:50 -0700\r\nDelivered-To: scatterpeas@gmail.com\r\nMessage-ID: <CAJVJxF1WiQOsMevi7QDcCO+qxuf4G5P05t60CheqeB_1dsqdmA@mail.gmail.com>\r\nSubject: cronjob\r\nFrom: Pea Body <scatterpeas@gmail.com>\r\nTo: Pea Body <scatterpeas@gmail.com>\r\nContent-Type: multipart/alternative; boundary=bcaec5489fb7d14ca2051ade2fbb\r\n\r\n--bcaec5489fb7d14ca2051ade2fbb\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n*/2 * * * * /Library/Frameworks/Python.framework/Versions/2.7/bin/python\r\n/Users/sakiukaji/Projects/feature_email/email_sender_gmail.py\r\n\r\n--bcaec5489fb7d14ca2051ade2fbb\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n<div dir="ltr">\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n<p class=""><span class="">*/2 * * * * /Library/Frameworks/Python.framework/Versions/2.7/bin/python /Users/sakiukaji/Projects/feature_email/email_sender_gmail.py</span></p></div>\r\n\r\n--bcaec5489fb7d14ca2051ade2fbb--'
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        imap_client = mock_imap.return_value
        imap_client.select.return_value = ('OK', ['36'])
        imap_client.search.return_value = ('OK', ['2 3 5 8 17 18 19 20 21 22'])
        imap_client.fetch.return_value = ('OK', [('22 (RFC822 {958}', expected), ' FLAGS (\\Seen))'])

        raw_email = get_email()
        assert raw_email == expected


def test_get_emaiil_select_fail():
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        imap_client = mock_imap.return_value
        imap_client.select.return_value = ('NO',
                                           ['[NONEXISTENT] Unknown Mailbox: nmr (now in authenticated state) (Failure)'])

        with pytest.raises(ValueError):
            get_email()


def test_get_emaiil_search_fail():
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        imap_client = mock_imap.return_value
        imap_client.select.return_value = ('OK', ['36'])
        imap_client.search.return_value = ('OK', [''])
        with pytest.raises(IndexError):
            get_email()


def test_send_sms():
    with patch('send_sms.TwilioRestClient') as mock_sms:
        instance = mock_sms.return_value
        instance.messages.create.side_effect = NotImplementedError('boom')
        with pytest.raises(NotImplementedError):
            send_sms(1, 2, 3)
