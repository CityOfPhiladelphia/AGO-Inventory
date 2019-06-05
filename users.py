from arcgis import GIS
import csv
import datetime
import smtplib
from email.mime.text import MIMEText
from configparser import ConfigParser
import logging
import socket

config = ConfigParser()
config.read('ago_config.ini')

# Logging variables
MAX_BYTES = config.get('logging', 'max_bytes')  # in bytes
# Max number appended to log files when MAX_BYTES reached
BACKUP_COUNT = config.get('logging', 'file_count')

# Create file logger (change logging level from default ERROR with the 'level' variable, i.e. DEBUG, INFO, WARN, ERROR, CRITICAL)
logging.basicConfig(filename='log.txt', level=logging.WARNING, format=('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger()


def sendemail(sender, subject, text, recipientslist):
    relay = config.get('email', 'relay')
    commaspace = ', '
    msg = MIMEText(text, 'html')
    msg['To'] = commaspace.join(recipientslist)
    msg['From'] = sender
    msg['X-Priority'] = '2'
    msg['Subject'] = subject
    server = smtplib.SMTP(relay)
    server.sendmail(sender, recipientslist, msg.as_string())
    server.quit()

email_sender = config.get('email', 'sender')
email_recipients = config.get('email', 'recipients').split(',')
email_subject = 'AGO Inventory Failure'

portal = config.get('ago', 'portal')
user = config.get('ago', 'user')
password = config.get('ago', 'password')
proxy = config.get('ago', 'proxy')
port = config.get('ago', 'port')

try:
    gis = GIS(portal, user, password, proxy=proxy, proxy_port=port)
    search = gis.users.search(query="", max_users=100000)

    li = []

    for x in search:
        try:
            li.append(
                [x.access, x.assignedCredits, x.availableCredits, x.created, x.description, x.email, x.id, x.idpUsername,
                 x.lastLogin, x.level, x.mfaEnabled, x.modified, x.role])
        except Exception as e:
            pass

    headers = ['access', 'assigned_credits', 'available_credits', 'created', 'description', 'email', 'id',
               'original_username', 'last_login', 'level', 'mfa_enabled', 'modified', 'role']

    year = datetime.datetime.today().strftime('%Y')
    month = datetime.datetime.today().strftime('%m')
    day = datetime.datetime.today().strftime('%d')
    file_suffix = str(year)+str(month)+str(day)


    file = r'users_'+file_suffix+'.csv'
    f = open(file, 'w', newline='', encoding='utf-8')
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(li)
except Exception as e:
    logger.error('AGO user inventory failed: ' + str(e))
    email_body = "AGO user inventory failure. Please see the log for details on server {}.".format(socket.gethostbyname(
        socket.gethostname()))
    sendemail(email_sender, email_subject, email_body, email_recipients)
