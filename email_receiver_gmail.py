#!/usr/bin/env python
# -*- coding: utf-8 -*-
import email
import imaplib


def get_email():
    username = ''
    password = ''

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, password)
    mail.select("inbox")
    result, data = mail.search(None, '(UNSEEN)')
    latest_email_uid = data[0].split()[-1]
    result, data = mail.fetch(latest_email_uid, '(RFC822)')
    raw_email = data[0][1]
    return raw_email


def process_email(raw_email):
    email_message = email.message_from_string(raw_email)
    toaddrs = email_message['To'].decode('UTF-8')
    fromaddr = email_message['From'].decode('UTF-8')
    print toaddrs
    print fromaddr
    maintype = email_message.get_content_maintype()
    if maintype == 'multipart':
        for part in email_message.get_payload():
            if part.get_content_maintype() == 'text':
                body = part.get_payload().decode('UTF-8')
                print body
                return email_message.get_payload()
    elif maintype == 'text':
        body = part.get_payload().decode('UTF-8')
        print body
        return email_message.get_payload()


def receive():
    raw_email = get_email()
    payload = process_email(raw_email)
    return payload


if __name__ == '__main__':
    receive()