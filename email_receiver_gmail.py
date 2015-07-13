#!/usr/bin/env python

import imaplib

username = 'scatterpeas'
password = 'peapassword'

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
