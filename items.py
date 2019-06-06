from arcgis import GIS
import pandas
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
    search = gis.content.search(query="", item_type="", max_items=100000)

    year = datetime.datetime.today().strftime('%Y')
    month = datetime.datetime.today().strftime('%m')
    day = datetime.datetime.today().strftime('%d')
    file_suffix = str(year)+str(month)+str(day)

    file = r'items_'+file_suffix+'.csv'

    df = pandas.DataFrame(search)
    df.to_csv(file, index=False)
except Exception as e:
    logger.error('AGO item inventory failed: '+str(e))
    email_body = 'AGO item inventory failure. Please see the log for details on server {}.'.format(
        socket.gethostbyname(socket.gethostname()))
    sendemail(email_sender, email_subject, email_body, email_recipients)
