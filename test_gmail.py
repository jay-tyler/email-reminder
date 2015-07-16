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
from twilio.rest import TwilioSMSManager
from twilio.rest import TwilioRestClient


def test_send_email():
    with patch('smtplib.SMTP') as mock_smtp:
        fromaddr = 'scatterpeas@gmail.com'
        toaddrs = 'scatterpeas@gmail.com'
        subject = 'Greeting'
        text = "This is text \n Hi!\nHow are you?\nI'm a scattered pea.\nhttps://www.youtube.com/watch?v=jHm0jmg-sbc"
        send(fromaddr, toaddrs, subject, text)
        instance = mock_smtp.return_value
        assert instance.sendmail.called is True
        assert instance.sendmail.call_count == 1


def test_receive_email():
    import pdb; pdb.set_trace()
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        mock_imap.login('scatterpeas', 'scatterpeas')
        mock_imap.select("inbox")
        instance = mock_imap.return_value
        # instance.search.return_value = ('OK', ['1 2 3 4'])
        # instance.fetch.return_value = ('OK', [('1 (RFC822 {6906}', 'MIME-Version: 1.0\r\nx-no-auto-attachment: 1\r\nReceived: by 10.25.146.77; Sun, 12 Jul 2015 14:36:13 -0700 (PDT)\r\nDate: Sun, 12 Jul 2015 14:36:13 -0700\r\nMessage-ID: <CAJVJxF0Ck0h2DYyDNJUB_AuWZY2yPZD5CyWbEmV-FDa-yzf8Fg@mail.gmail.com>\r\nSubject: Three tips to get the most out of Gmail\r\nFrom: Gmail Team <mail-noreply@google.com>\r\nTo: Pea Body <scatterpeas@gmail.com>\r\nContent-Type: multipart/alternative; boundary=f46d042ef3e5ebc26a051ab464c1\r\n\r\n--f46d042ef3e5ebc26a051ab464c1\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n Three tips to get the most out of Gmail\r\n[image: Google]\r\n\r\nHi Pea\r\n\r\nTips to get the most out of Gmail\r\n\r\n[image: Contacts]\r\nBring your contacts and mail into Gmail\r\n\r\nOn your computer, you can copy your contacts and emails from your old email\r\naccount to make the transition to Gmail even better. Learn how\r\n<https://support.google.com/mail/answer/164640?hl=3Den&ref_topic=3D1669014>=\r\n.\r\n[image: Search]\r\nFind what you need fast\r\n\r\nWith the power of Google Search right in your inbox, it\'s easy to sort your\r\nemail. Find what you\'re looking for with predictions based on email\r\ncontent, past searches and contacts.\r\n[image: Search]\r\nMuch more than email\r\n\r\nYou can send text messages and make video calls with Hangouts\r\n<https://www.google.com/intl/en/hangouts/> right from Gmail. To use this\r\nfeature on mobile, download the Hangouts app for Android\r\n<https://play.google.com/store/apps/details?id=3Dcom.google.android.talk&hl=\r\n=3Den>\r\nand Apple <https://itunes.apple.com/en/app/hangouts/id643496868?mt=3D8>\r\ndevices.\r\n\r\n\r\n[image: Gmail icon]Happy emailing,\r\nThe Gmail Team\r\n =C2=A9 2015 Google Inc. 1600 Amphitheatre Parkway, Mountain View, CA 94043\r\n\r\n--f46d042ef3e5ebc26a051ab464c1\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n<!DOCTYPE html>\r\n<html><head><meta http-equiv=3D"content-type" content=3D"text/html;charset=\r\n=3DUTF-8" /><title>Three tips to get the most out of Gmail</title></head><b=\r\nody style=3D"background-color:#e5e5e5; margin:20px 0;"><br /><div style=3D"=\r\nmargin:2%;"><div style=3D"direction:ltr; text-align:left; font-family:\'Open=\r\n sans\',\'Arial\',sans-serif; color:#444; background-color:white; padding:1.5e=\r\nm; border-radius:1em; box-shadow:1px -5px 8px 2px #bbb; max-width:580px; ma=\r\nrgin:2% auto 0 auto;"><table style=3D"background:white;width:100%"><tr><td>=\r\n<div style=3D"width:90px; height:54px; margin:10px auto;"><img src=3D"https=\r\n://services.google.com/fh/files/emails/google_logo_flat_90_color.png" alt=\r\n=3D"Google" width=3D"90" height=3D"34"/></div><div style=3D"width:90%; padd=\r\ning-bottom:10px; padding-left:15px"><p><img alt=3D"" aria-hidden=3D"true" s=\r\nrc=3D"https://ssl.gstatic.com/ui/v1/icons/mail/images/gmail_logo_large.png"=\r\n style=3D"display:inline-block; max-height:10px; margin-right:5px;"/><span =\r\nstyle=3D"font-family:\'Open sans\',\'Arial\',sans-serif; font-weight:bold; font=\r\n-size:small; line-height:1.4em">Hi Pea</span></p><p><span style=3D"font-fam=\r\nily:\'Open sans\',\'Arial\',sans-serif; font-size:2.08em;">Tips to get the most=\r\n out of Gmail</span><br/></p></div><p></p><div style=3D"float:left; clear:b=\r\noth; padding:0px 5px 10px 10px;"><img src=3D"https://services.google.com/fh=\r\n/files/emails/importcontacts.png" alt=3D"Contacts" style=3D"display:block;"=\r\nwidth=3D"129"height=3D"129"/></div><div style=3D"float:left; vertical-align=\r\n:middle; padding:10px; max-width:398px; float:left;"><table style=3D"vertic=\r\nal-align:middle;"><tr><td style=3D"font-family:\'Open sans\',\'Arial\',sans-ser=\r\nif;"><span style=3D"font-size:20px;">Bring your contacts and mail into Gmai=\r\nl</span><br/><br/><span style=3D"font-size:small; line-height:1.4em">On you=\r\nr computer, you can copy your contacts and emails from your old email accou=\r\nnt to make the transition to Gmail even better. <a href=3D"https://support.=\r\ngoogle.com/mail/answer/164640?hl=3Den&amp;ref_topic=3D1669014" style=3D"tex=\r\nt-decoration:none; color:#15C">Learn how</a>.</span></td></tr></table></div=\r\n><div style=3D"float:left; clear:both; padding:0px 5px 10px 10px;"><img src=\r\n=3D"https://ssl.gstatic.com/mail/welcome/localized/en/welcome_search.png" a=\r\nlt=3D"Search" style=3D"display:block;"width=3D"129"height=3D"129"/></div><d=\r\niv style=3D"float:left; vertical-align:middle; padding:10px; max-width:398p=\r\nx; float:left;"><table style=3D"vertical-align:middle;"><tr><td style=3D"fo=\r\nnt-family:\'Open sans\',\'Arial\',sans-serif;"><span style=3D"font-size:20px;">=\r\nFind what you need fast</span><br/><br/><span style=3D"font-size:small; lin=\r\ne-height:1.4em">With the power of Google Search right in your inbox, it\'s e=\r\nasy to sort your email. Find what you\'re looking for with predictions based=\r\n on email content, past searches and contacts.</span></td></tr></table></di=\r\nv><div style=3D"float:left; clear:both; padding:0px 5px 10px 10px;"><img sr=\r\nc=3D"https://ssl.gstatic.com/accounts/services/mail/msa/welcome_hangouts.pn=\r\ng" alt=3D"Search" style=3D"display:block;"width=3D"129"height=3D"129"/></di=\r\nv><div style=3D"float:left; vertical-align:middle; padding:10px; max-width:=\r\n398px; float:left;"><table style=3D"vertical-align:middle;"><tr><td style=\r\n=3D"font-family:\'Open sans\',\'Arial\',sans-serif;"><span style=3D"font-size:2=\r\n0px;">Much more than email</span><br/><br/><span style=3D"font-size:small; =\r\nline-height:1.4em">You can send text messages and make video calls with <a =\r\nhref=3D"https://www.google.com/intl/en/hangouts/" style=3D"text-decoration:=\r\nnone; color:#15C">Hangouts</a> right from Gmail. To use this feature on mob=\r\nile, download the Hangouts app for <a href=3D"https://play.google.com/store=\r\n/apps/details?id=3Dcom.google.android.talk&amp;hl=3Den" style=3D"text-decor=\r\nation:none; color:#15C">Android</a> and <a href=3D"https://itunes.apple.com=\r\n/en/app/hangouts/id643496868?mt=3D8" style=3D"text-decoration:none; color:#=\r\n15C">Apple</a> devices.</span></td></tr></table></div><br/><br/>\r\n<div style=3D"clear:both; padding-left:13px; height:6.8em;"><table style=3D=\r\n"width:100%; border-collapse:collapse; border:0"><tr><td style=3D"width:68p=\r\nx"><img alt=3D\'Gmail icon\' width=3D"49" height=3D"37" src=3D"https://ssl.gs=\r\ntatic.com/ui/v1/icons/mail/images/gmail_logo_large.png" style=3D"display:bl=\r\nock;"/></td><td style=3D"align:left; font-family:\'Open sans\',\'Arial\',sans-s=\r\nerif; vertical-align:bottom"><span style=3D"font-size:small">Happy emailing=\r\n,<br/></span><span style=3D"font-size:x-large; line-height:1">The Gmail Tea=\r\nm</span></td></tr></table></div>\r\n</td></tr></table></div>\r\n<div style=3D"direction:ltr;color:#777; font-size:0.8em; border-radius:1em;=\r\n padding:1em; margin:0 auto 4% auto; font-family:\'Arial\',\'Helvetica\',sans-s=\r\nerif; text-align:center;">=C2=A9 2015 Google Inc. 1600 Amphitheatre Parkway=\r\n, Mountain View, CA 94043<br/></div></div></body></html>\r\n\r\n--f46d042ef3e5ebc26a051ab464c1--'), ')'])
        # # receive()
        get_email()
        # process_email()
        receive()
        assert instance.search.return_value == ('OK', ['1 2 3 4'])
        # raw_email = get_email()
        # raw_email = data[0][1]
        # assert len(raw_email) > 0
        # assert instance.search.return_value == ('OK', ['1 2 3 4'])
        # assert instance.list()[0] == 'OK'
        # assert len(instance.login('scatterpeas', 'scatterpeas')) == 2
        # assert instance.list()[0] == 'OK'


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


# def test_send_sms():
#     """Test the Twilio API."""
#     info_dict = {'Body': 'this is a test text', 'To': '+14251234567', 'From': '+12061234567'}
#     expected_response_dict = {'account_sid': "AC82fab74047ef173da0a573a020858a59",
#                               'body': 'Jenny please?! I love you <3',
#                               'from': '+16319564194',
#                               'to': '+12069542208',
#                               }
#     sms = TwilioSMSManager()
#     # Mock responses from Twilio.
#     with mock.patch('tornado.httpclient.AsyncHTTPClient', MockAsyncHTTPClient()) as mock_client:
#       # Response to sms.
#       _AddMockJSONResponse(mock_client,
#                            r'https://api.twilio.com/2010-04-01/Accounts/dummy_twilio_account_sid/SMS/Messages.json',
#                            expected_response_dict
#                           )
#       response_dict = self._RunAsync(sms.SendSMS, number=info_dict['To'], text=info_dict['Body'])
#       assert expected_response_dict == response_dict
    # mail = imaplib.IMAP4_SSL("imap.gmail.com")
    # assert mail.list()[0] == 'OK'
    # assert len(mail.list()) == 2
    # assert type(mail.list()[1]) == int

    # assert mail.select('INBOX') == 'OK'
    # assert len(mail.select('INBOX')) == 2
    # assert type(mail.select('INBOX')[1]) == int



# def test_receive_fetch():
#     mail = imaplib.IMAP4_SSL("imap.gmail.com")
#     assert mail.fetch('1', '(BODY[HEADER])') is not None
#     assert mail.fetch('1', '(BODY[TEXT])') is not None
#     assert mail.fetch('1', '(FLAGS)') is not None
    # assert len(mail.list()) == 2
    # assert type(mail.list()[1]) == int
    # obj = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    # obj.login('username', 'password')
    # obj.select('**label name**') # <-- the label in which u want to search message
    # obj.search(None, 'FROM', '"LDJ"')




# @pytest.fixture()
# def send_email():
#     fromaddr = 'scatterpeas@gmail.com'
#     toaddrs = 'scatterpeas@gmail.com'
#     subject = 'Greeting'
#     text = "This is text \n Hi!\nHow are you?\nI'm a scattered pea.\nhttps://www.youtube.com/watch?v=jHm0jmg-sbc"
#     html = """
#     <html>
#       <head></head>
#       <body>
#         <p>Hi!<br>
#             This is HTML<br>
#             How are you?<br>
#             I'm a scattered pea. <a href="https://www.youtube.com/watch?v=jHm0jmg-sbc">Watch this</a>
#         </p>
#       </body>
#     </html>
#      """
#     # attachment = 'nmr.jpg'
#     send(fromaddr, toaddrs, subject, text, html)

#     username = 'scatterpeas@gmail.com'
#     password = 'peapassword'

#     mail = imaplib.IMAP4_SSL("imap.gmail.com")
#     mail.login(username, password)
#     mail.list()
#     mail.select("inbox")
#     result, data = mail.uid('search', None, "ALL")
#     latest_email_uid = data[0].split()[-1]
#     result, data = mail.uid('fetch', latest_email_uid, '(RFC822)')
#     raw_email = data[0][1]
#     return raw_email


# def test_send(send_email):

#     assert 'scatterpeas@gmail.com' in raw_email
#     assert 'scatterpeas@gmail.com' in raw_email
    # assert 'Greeting' in raw_email
    # assert text in raw_email
    # assert html in raw_email
    # print raw_email
    # mail = imaplib.IMAP4_SSL("imap.gmail.com")
    # assert mail.list()[0] == 'OK'
    # assert len(mail.list()) == 2
    # assert type(mail.list()[1]) == int


# def test_receive_mailbox():
#     mail = imaplib.IMAP4_SSL("imap.gmail.com")
#     assert mail.select('INBOX') == 'OK'
#     assert len(mail.select('INBOX')) == 2
#     assert type(mail.select('INBOX')[1]) == int


# def test_receive_fetch():
#     mail = imaplib.IMAP4_SSL("imap.gmail.com")
#     assert mail.fetch('1', '(BODY[HEADER])') is not None
#     assert mail.fetch('1', '(BODY[TEXT])') is not None
#     assert mail.fetch('1', '(FLAGS)') is not None

# def test_parse_email()