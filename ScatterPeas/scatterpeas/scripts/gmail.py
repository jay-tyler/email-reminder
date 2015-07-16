#!/usr/bin/env python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage

import imaplib

with open('ScatterPeas/scatterpeas/scripts/gmail_creds.txt', 'r') as fh:
    username = fh.readline()
    password = fh.readline()


def send(fromaddr, toaddrs, subject='no subject', text='', html=None, img=None):
    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject
    msg['From'] = fromaddr
    msg['To'] = toaddrs

    if img is not None:
        fp = open(img, 'rb')
        part3 = MIMEImage(fp.read())
        fp.close()
        msg.attach(part3)
    else:
        pass

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    msg.attach(part1)
    msg.attach(part2)

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username, password)
    server.sendmail(fromaddr, toaddrs, msg.as_string())
    server.quit()


def receive():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")

    mail.login(username, password)
    mail.list()
    mail.select("inbox")

    result, data = mail.uid('search', None, "ALL")
    latest_email_uid = data[0].split()[-1]
    result, data = mail.uid('fetch', latest_email_uid, '(RFC822)')
    raw_email = data[0][1]
    print raw_email
    mail.logout()

if __name__ == '__main__':
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
    #img = 'nmr.jpg'
    send(fromaddr, toaddrs, subject, text, html)

    receive()
