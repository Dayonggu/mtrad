import smtplib
from email.mime.text import MIMEText
from systemconfig import sysconst as sc

def send_email(message):
    try:
        msg = MIMEText(message)
        msg['Subject'] = 'trc report'
        msg['From'] = sc.sender
        msg['To'] = sc.receiver
        smtpObj = smtplib.SMTP('localhost')
        s = smtplib.SMTP('localhost')
        s.sendmail(sc.sender, [sc.receiver], msg.as_string())
        s.quit()
        print "Successfully sent email"
    except Exception:
        print "Error: unable to send email"
