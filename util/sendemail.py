import smtplib
import json,os,sys
from email.mime.text import MIMEText
from systemconfig import sysconst as sc

config = json.loads(open(sc.CONFIG_HOME+"/email_setting.json").read())

email_user = config['email_user']
email_pass = config['email_pass']
email_server = config['email_server']


def send_email(subject, message):

    #email_text = '"From:{} To:{} Subject:{} {}"'.format(email_user,email_user,subject,message)

    try:
        server = smtplib.SMTP(email_server, 587)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, email_user, message)
        server.quit()        
        print "Successfully sent email"
    except Exception as err:
        print 'Error: unable to send email:{}'.format(err)
    finally:
        server.quit()
