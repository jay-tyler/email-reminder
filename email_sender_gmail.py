import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage


def main(fromaddr, toaddrs, subject, text, html, img):
    msg = MIMEMultipart('mixed')
    # msg = MIMEText("I'm scattered")
    msg['Subject'] = subject
    msg['From'] = fromaddr
    msg['To'] = toaddrs

    fp = open(img, 'rb')
    part3 = MIMEImage(fp.read())
    fp.close()

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    msg.attach(part1)
    msg.attach(part2)
    msg.attach(part3)

    username = 'scatterpeas@gmail.com'
    password = 'peapassword'
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username, password)
    server.sendmail(fromaddr, toaddrs, msg.as_string())
    server.quit()

if __name__ == '__main__':
    fromaddr = 'scatterpeas@gmail.com'
    toaddrs = 'saki.fu86@gmail.com'
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
    img = 'nmr.jpg'
    main(fromaddr, toaddrs, 'title', text, html, img)

