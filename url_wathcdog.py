import os
import subprocess
import requests
import socket
import time
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import json
import signal
import sys
from dotenv import load_dotenv

# Define a function to print the script's logo
def print_logo():
    print(r"""
 _____            _       _   _          _______        _
|  __ \          | |     | | (_)        |__   __|      | |
| |  | |___  ___ | |_   _| |_ _  ___  _ __ | | ___  ___| |__
| |  | / __|/ _ \| | | | | __| |/ _ \| '_ \| |/ _ \/ __| '_ '\
| |__| \__ \ (_) | | |_| | |_| | (_) | | | | |  __/ (__| | | |
|_____/|___/\___/|_|\__,_|\__|_|\___/|_| |_|_|\___|\___|_| |_|
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                |M|o||n|i|t|o||r|_|U|p|t|i|m|e|
                +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
""")

print_logo()

# Define the path to the websites configuration file
WEBSITES_CONFIG_FILE = '/workspaces/python-applications/webapp/URL_WatchDog/config/websites_config.json'

load_dotenv()

# Set up logging
LOGGING_FORMAT = '%(asctime)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)

# Set up WhatsApp API credentials
WHATSAPP_API_TOKEN = os.environ.get('WHATSAPP_API_TOKEN')
WHATSAPP_CHAT_ID = os.environ.get('WHATSAPP_CHAT_ID')
WHATSAPP_INSTANCE_ID = os.environ.get('WHATSAPP_INSTANCE_ID')
WHATSAPP_URL = f'https://7103.api.greenapi.com/waInstance{WHATSAPP_INSTANCE_ID}/sendMessage/{WHATSAPP_API_TOKEN}'
headers = {'Content-Type': 'application/json'}

# Function to send a message to WhatsApp using the WhatsApp API
def send_message(message):
    data = {"chatId": WHATSAPP_CHAT_ID, "message": message}
    try:
        response = requests.post(WHATSAPP_URL, headers=headers, json=data)
        if response.status_code == 200:
            logger.info(f'Message sent to {WHATSAPP_CHAT_ID}')
        else:
            logger.error(f'Failed to send message to {WHATSAPP_CHAT_ID}')
            logger.error(response.text)
    except Exception as e:
        logger.error(f'Error sending message: {str(e)}')
        
# Function to read the websites configuration from the config file
def read_websites_from_config():
    with open(WEBSITES_CONFIG_FILE, 'r') as file:
        return json.load(file)
        
# Function to get the status icon based on the status of a website (UP or DOWN)
def get_status_icon(status):
    return '✅' if status == 'UP' else '🔴'

# Function to check if a host is up using ICMP ping
def ping_host(host):
    try:
        result = subprocess.run(['ping', '-c', '1', host], stdout=subprocess.PIPE, timeout=1)
        return result.returncode == 0
    except Exception as e:
        return False
        
# Function to check if a website is up by checking its response code and keyword 
def check_website(url, keyword):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=2, verify=False)
        end_time = time.time()

        if response.status_code == 200 and keyword in response.text:
            return True, end_time - start_time
        else:
            return False, None
    except requests.exceptions.RequestException as e:
        logger.error(f'Error checking website: {str(e)}')
        return False, None
        
# Function to perform a TCP ping (connect to a host and port)
def tcp_ping(hostname, port):
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((hostname, port))
        end_time = time.time()
        sock.close()
        response_time = end_time - start_time
        return True, response_time
    except Exception as e:
        logger.error(f'Error with TCP ping: {str(e)}')
        return False, None

# Function to monitor a website's status and send notifications if it changes
def monitor_website(website):
    url = website['url']
    log_file = f'{website["name"].lower().replace(" ", "_")}.log'
    logger_name = f'{website["name"]}_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    logger = logging.getLogger(logger_name)
    file_handler = RotatingFileHandler('/workspaces/python-applications/webapp/URL_WatchDog/Logs/' + log_file, maxBytes=1000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if ':' not in url:
        status = ping_host(url)
    else:
        if 'keyword' in website:
            status, response_time = check_website(url, website['keyword'])
        else:
            port = int(url.split(':')[-1])
            hostname = url.split('//')[-1].split(':')[0]
            status, response_time = tcp_ping(hostname, port)

    if status:
        status_msg = 'UP'
    else:
        status_msg = 'DOWN'

    if ':' not in url:
        logger.info(f'PING {"successful" if status else "failed"}, {website["name"]} is {status_msg}')
    else:
        if response_time is not None:
            logger.info(f'Keyword found, {website["name"]} is UP. Response time: {response_time:.2f} seconds')
        else:
            logger.info(f'Keyword not found, {website["name"]} is DOWN')

    if status != previous_statuses.get(website["name"], False):
        if status:
            send_message(f'[{website["name"]} {get_status_icon("UP")}] is UP')
        else:
            send_message(f'[{website["name"]} {get_status_icon("DOWN")}] is DOWN')

    file_handler.close()
    logger.removeHandler(file_handler)

    return status

previous_statuses = {website["name"]: True for website in read_websites_from_config()}

# Define a signal handler for SIGTERM and SIGINT signals
def signal_handler(signum, frame):
    try:
        exception = sys.exc_info()[1]
    except Exception as e:
        exception = e

    with open('/workspaces/python-applications/webapp/URL_WatchDog/Logs/error.log', 'a') as f:
        now = datetime.now()
        f.write(f'Script terminated at {now.strftime("%Y-%m-%d %H:%M:%S")}\n')
        if signum == signal.SIGINT:
            f.write('Reason: Interrupted by user\n')
        elif signum == signal.SIGTERM:
            f.write('Reason: Terminated by signal\n')
        if exception:
            f.write(f'Error: {str(exception)}\n')
            f.write(f'Error occurred in {sys._getframe().f_code.co_filename} at line {sys._getframe().f_lineno}\n')

    message = f'SCRIPT TERMINATED. PLEASE SEE ERROR LOG.'
    send_message(message)

    sys.exit(1)

# Install the signal handler for SIGTERM and SIGINT signals
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

while True:
    try:
        for website in read_websites_from_config():
            current_status = monitor_website(website)
            previous_statuses[website["name"]] = current_status

        time.sleep(30)

    except Exception as e:
        pass
