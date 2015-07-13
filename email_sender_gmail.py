import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

fromaddr = 'scatterpeas@gmail.com'
toaddrs = 'saki.fu86@gmail.com'

msg = MIMEMultipart('alternative')
# msg = MIMEText("I'm scattered")
msg['Subject'] = "Greeting"
msg['From'] = fromaddr
msg['To'] = toaddrs

text = "This is text \n Hi!\nHow are you?\nI'm a scattered pea.\nhttps://www.codefellows.org/"
html = """
<html>
  <head></head>
  <body>
    <p>Hi!<br>
        This is HTML<br>
        How are you?<br>
        I'm a scattered pea. <a href="https://www.codefellows.org/">Watch this</a>
    </p>
  </body>
</html>
 """
part1 = MIMEText(text, 'plain')
part2 = MIMEText(html, 'html')

msg.attach(part1)
msg.attach(part2)

username = 'scatterpeas@gmail.com'
password = 'peapassword'
server = smtplib.SMTP('smtp.gmail.com:587')
server.starttls()
server.login(username, password)
server.sendmail(fromaddr, toaddrs, msg.as_string())
server.quit()