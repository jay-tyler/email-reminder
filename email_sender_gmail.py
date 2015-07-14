#!/usr/bin/env python
# -*- coding: utf-8 -*-
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage


def send(fromaddr, toaddrs, subject='no subject', text='', html=None, attachment=None):
    msg = MIMEMultipart('mixed')
    msg.set_charset("utf-8")
    msg['Subject'] = subject
    msg['From'] = fromaddr
    msg['To'] = toaddrs

    if attachment is not None:
        fp = open(attachment, 'rb')
        part3 = MIMEImage(fp.read())
        fp.close()
        msg.attach(part3)
    else:
        pass

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    msg.attach(part1)
    msg.attach(part2)

    username = ''
    password = ''
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username, password)
    server.sendmail(fromaddr, toaddrs, msg.as_string())
    server.quit()

if __name__ == '__main__':
    fromaddr = ''
    toaddrs = ''
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

