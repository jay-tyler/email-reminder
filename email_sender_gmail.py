import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

fromaddr = 'scatterpeas@gmail.com'
toaddrs = 'saki.fu86@gmail.com'

msg = MIMEText("I'm scattered")
msg['Subject'] = "Greeting"
msg['From'] = fromaddr
msg['To'] = toaddrs

username = 'scatterpeas@gmail.com'
password = 'peapassword'
server = smtplib.SMTP('smtp.gmail.com:587')
server.starttls()
server.login(username, password)
server.sendmail(fromaddr, toaddrs, msg.as_string())
server.quit()