#!/usr/bin/env python

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime

import requests
from dateutil import parser
from dateutil.relativedelta import relativedelta
from retry import retry
from loguru import logger

logger.add(sys.stdout, format='{time} {level} {message}', filter='bus_notify', level='INFO')
logger.add(f'/tmp/bus_notify_{time}.log')
logger.add('/tmp/bus_notify_1.log', rotation='500 MB')

TMPDIR = '/tmp'
CONTROL_FILE_URL = 'https://dl.dropboxusercontent.com/s/z3pd6zuyl5ckwy1/control.json'
CONTROL_JSON_PATH = os.path.join(TMPDIR, 'control.json')

# URLs
NOTIFICATION_URL = 'https://api.pushover.net/1/messages.json?token=a6dvutumicnvuo7mhs1twnhisacwtb&user=u9iun1uiaz6cch9uyr6m2uu8hrywd8&message={text}'
BASE_URL = 'http://curlbus.app/'

# Bus stops IDs and line numbers
HOME_BUS_STOP_ID = '33326'
WORK_BUS_STOP_ID = '25141'
BUS_LINE_NAMES = ['74', '174']

URL_TO_HOME = os.path.join(BASE_URL, WORK_BUS_STOP_ID)
URL_TO_WORK = os.path.join(BASE_URL, HOME_BUS_STOP_ID)

MIDWEEK_DAYS = (0, 1, 2, 3, 6)  # Mon, Tue, Wed, Thu, Sun
SECONDS_IN_DAY = 24 * 60 * 60
INTERVAL_BETWEEN_NOTIFICATIONS = 120
COMMAND_POLL_INTERVAL = 10
STOP_NOTIFICATION_SENT = False


def send_notification(text: str):
    url = NOTIFICATION_URL.format(text=text)
    res = requests.post(url)
    assert res.status_code == 200
    logger.info(f'Notification content:\n{text}')


def get_bus_arrival_minutes_remained(eta):
    eta_str = eta.split('+')[0]  # Remove time offset
    eta = parser.parse(eta_str)
    now = datetime.now()

    minutes_remained = relativedelta(eta, now).minutes
    if minutes_remained < 5:
      minutes_remained = f'🔜 {minutes_remained}'
    return minutes_remained


def get_bus_eta(url, bus_stop_id):
    etas = []

    try:
        res = requests.get(url, headers={'Accept': 'application/json'})
        res_json = res.json()
    except:
        return 'Curlbus does not respond 🤔'

    bus_stop_name = res_json['stop_info']['name']['EN']
    lines_info = res_json['visits'][bus_stop_id]

    for info in lines_info:
        line_name = info['line_name']
        if line_name in BUS_LINE_NAMES:
            bus_arrival_minutes_remained = get_bus_arrival_minutes_remained(info['eta'])
            etas.append(f'🚌 {line_name}: {bus_arrival_minutes_remained} min')

    if etas:
        etas_str = '\n'.join(etas)
        return f'{bus_stop_name}\n\n{etas_str}'
    return 'No buses :('


def is_weekend():
    return datetime.now.weekday() not in MIDWEEK_DAYS


@retry(Exception, tries=50, delay=0.25)
def get_control_file():
    res = requests.get(CONTROL_FILE_URL, timeout=2, allow_redirects=True)
    with open(CONTROL_JSON_PATH, 'wb') as f:
        f.write(res.text.encode('utf-8'))

    return res.json()


def main():

    global STOP_NOTIFICATION_SENT

    while True:
        control_json = get_control_file()

        # Terminate app if requested
        if control_json['command'] == 'terminate':
            send_notification('Terminating the app')
            sys.exit(1)

        # Handle there is no control file
        if not os.path.isfile(CONTROL_JSON_PATH) or \
                control_json['command'] == 'stop' or \
                not control_json.get('location'):
            logger.info(f'Nothing to do. Waiting for commands')
            if not STOP_NOTIFICATION_SENT:
                send_notification('App is stopped')
                STOP_NOTIFICATION_SENT = True

            time.sleep(COMMAND_POLL_INTERVAL)
            continue

        # Decide the direction of the bus
        url = URL_TO_HOME
        station_id = WORK_BUS_STOP_ID
        if control_json['location'] == 'home':
            url = URL_TO_WORK
            station_id = HOME_BUS_STOP_ID

        # Get ETA, send notification and wait for 120 seconds
        eta = get_bus_eta(url, station_id)
        send_notification(eta)
        time.sleep(INTERVAL_BETWEEN_NOTIFICATIONS)


if __name__ == '__main__':
    main()
