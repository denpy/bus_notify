#
# Copyright 2020. All rights reserved.
#
from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from dateutil import parser
from dateutil.relativedelta import relativedelta
from retry.api import retry_call

# Configure a minimal logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s:%(levelname)s: %(message)s')


class BusEtaNotifier(object):
    """
    FOO
    """

    CURLBUS_BASE_URL = 'http://curlbus.app/'
    SECONDS_IN_MINUTE = 60
    CURLBUS_QUERY_INTERVAL = 120

    # noinspection PyShadowingNames
    def __init__(self, logger=logger):
        self.logger = logger

    def _get_bus_etas(self, station_id: str, line_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        etas = []

        # Get the data from Curlbus
        url = os.path.join(self.CURLBUS_BASE_URL, station_id)
        res = requests.get(url, headers={'Accept': 'application/json'}, timeout=60)
        res_json = res.json()

        lines_info = res_json['visits'][station_id]

        for info in lines_info:
            line_name = int(info['line_name'])  # Curlbus calls the line number as "line_name" (str type)
            if line_names and line_name not in line_names:
                continue

            # Get how many minutes left from now until the bus arrives to the station
            eta = relativedelta(parser.parse(info['eta']), datetime.now()).minutes
            for e in etas:
                if line_name == e['line_name']:
                    e['etas'].append(eta)
                    continue

            etas.append(dict(stattion_name=res_json['stop_info']['name']['EN'], line_name=line_name, etas=[eta]))

        return etas

    def _notify(self):
        control = self.get_control_dict()

        # Validate "station_id" field exists
        if not ('station_id' in control and control['station_id']):
            err_msg = '"station_id" field must be not empty'
            self.logger.error(err_msg)
            raise ValueError(err_msg)

        self.etas = self._get_bus_etas(control['station_id'], control.get('lines'))
        self.send_notification()

    def run(self, service_query_interval=CURLBUS_QUERY_INTERVAL):
        while True:
            try:
                retry_call(self._notify, tries=10, delay=6, max_delay=3 * self.SECONDS_IN_MINUTE, logger=self.logger)
            except Exception as exc:
                self.logger.error(f'Failed to get data from Curlbus service. Reason: {exc}')
            self.logger.info(f'Next attempt to get ETA is in {service_query_interval} seconds.')
            time.sleep(service_query_interval)

    def get_control_dict(self) -> Dict[str, Any]:
        """
        Get a dict which contains an info for querying Curlbus service.
        Control dict fields:
        - "station_id" (mandatory) is a number that represents the bus station ID (can be found using Google maps)
        - "lines" (optional) is a list of lines user is interested to get ETAs, if empty or not provided all lines ETAs
          will be returned
        Example:
            {'station_id': 33326, 'lines': [74, 174]}
        :return: a dict with info for querying Curlbus service
        """
        return {'station_id': '25141'}  # FOO
        # raise NotImplementedError

    def send_notification(self):
        """
        Send a notification with bus ETAs
        """
        # raise NotImplementedError
        print(self.etas)  # FOO
