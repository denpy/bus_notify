#
# Copyright 2020. All rights reserved.
#
from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from typing import Any, Dict

import requests
from dateutil import parser
from dateutil.relativedelta import relativedelta
from loguru import logger as loguru_logger
from retry.api import retry_call


class BusEtaNotifier(object):
    """
    FOO
    """

    CURLBUS_BASE_URL = 'http://curlbus.app/'
    SECONDS_IN_DAY = 24 * 60 * 60
    CURLBUS_QUERY_INTERVAL = 120
    WAIT_4_ACTION_INTERVAL = 10
    STOP_NOTIFICATION_SENT = False

    def __init__(self, logger=None):
        if logger is None:
            logger = loguru_logger
            logger.add(sys.stdout, format='{time} {level} {message}', filter='bus_notify', level='INFO')
            # logger.add('/tmp/bus_notify_1.log', rotation='500 MB')  FOO
        self.logger = logger

    def _get_bus_etas(self, station_id, line_names):
        etas = []

        # Get the data from Curlbus
        url = os.path.join(self.CURLBUS_BASE_URL, station_id)
        res = requests.get(url, headers={'Accept': 'application/json'}, timeout=60)
        res_json = res.json()

        station_name = res_json['stop_info']['name']['EN']
        lines_info = res_json['visits'][station_id]

        for info in lines_info:
            line_name = info['line_name']  # Curlbus calls the line number as "line_name"
            if line_names and line_name not in line_names:
                continue

            # Get how many minutes left until bus arrives to the station
            eta = relativedelta(parser.parse(info['eta']), datetime.now()).minutes
            for e in etas:
                if line_name == e['line_name']:
                    e['etas'].append(eta)
                    continue

            etas.append(dict(stattion_name=station_name, line_name=int(line_name), etas=[eta]))

        return etas

    def _notify(self):
        control = self.get_control_dict()
        self.etas = self._get_bus_etas(control['station_id'], control['lines'])
        self.send_notification()

    def run(self):
        while True:
            try:
                retry_call(self._notify, tries=10, delay=6, max_delay=180, logger=self.logger)
            except Exception as exc:
                self.logger.error(f'Failed to get data from Curlbus service. Reason: {exc}')
            self.logger.info(f'Next attempt to get ETA is in {self.CURLBUS_QUERY_INTERVAL} seconds.')
            time.sleep(self.CURLBUS_QUERY_INTERVAL)

    def get_control_dict(self) -> Dict[str, Any]:
        """
        FOO
        cmd options: start, stop, terminate
        :return: {'cmd': 'start', 'station_id': 33326, 'lines': [74, 174]}
        """
        return {'cmd': 'start', 'station_id': '25141', 'lines': []}
        # raise NotImplementedError

    def send_notification(self):
        """
        FOO
        :return:
        """
        # raise NotImplementedError
        print(self.etas)
