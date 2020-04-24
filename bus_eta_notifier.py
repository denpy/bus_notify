#
# Copyright 2020. All rights reserved.
#
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from dateutil import parser
from dateutil.relativedelta import relativedelta
from retry.api import retry_call

# Configure a minimal logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s:%(levelname)s: %(message)s')


class BusEtaNotifier(ABC):
    """
    FOO
    """

    CURLBUS_BASE_URL = 'http://curlbus.app/'
    SECONDS_IN_MINUTE = 60
    CURLBUS_QUERY_INTERVAL = 2 * SECONDS_IN_MINUTE

    # noinspection PyShadowingNames
    def __init__(self, logger=logger):
        self.logger = logger

    def _get_bus_etas(self, station_id: str, line_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        etas = []

        # Get the data from Curlbus
        station_id = str(station_id)
        url = urljoin(self.CURLBUS_BASE_URL, station_id)
        res = requests.get(url, headers={'Accept': 'application/json'}, timeout=60)
        res_json = res.json()
        # print(res_json)

        eta_obj = dict(stattion_name=res_json['stop_info']['name']['EN'], errors=None)
        errors = res_json['errors']
        if errors is not None:
            eta_obj['errors'] = errors
            etas.append(eta_obj)

        for info in res_json['visits'][station_id]:
            line_name = int(info['line_name'])  # Curlbus calls the line number as "line_name" (str type)
            if line_names and line_name not in line_names:
                continue

            # Calculate how many minutes left from now until the bus arrives to the station
            eta = relativedelta(parser.parse(info['eta']), datetime.now()).minutes

            # Check maybe we already have an ETA for this line
            for e in etas:
                if line_name == e['line_name']:
                    # We already have ETA for this line, let's append an another one to it
                    e['etas'].append(eta)
                    continue

            # Update an object that contains an ETA info for this line and append it to the list of all ETAs
            eta_obj['line_name'] = line_name
            eta_obj['etas'] = [eta]
            etas.append(eta_obj)

        return etas

    def _notify(self):
        control = self.get_control_dict()

        # Validate "station_id" field exists
        if not ('station_id' in control and control['station_id']):
            err_msg = '"station_id" field must not be empty'
            self.logger.error(err_msg)
            raise ValueError(err_msg)

        self.etas = self._get_bus_etas(control['station_id'], control.get('lines'))
        self.send_notification()

    def run(self, service_query_interval=CURLBUS_QUERY_INTERVAL):
        while True:
            try:
                retry_call(
                    self._notify,
                    tries=6,
                    delay=10,
                    max_delay=2 * self.SECONDS_IN_MINUTE,
                    logger=self.logger)
            except Exception as exc:
                self.logger.error(f'Failed to get data from Curlbus service. Reason: {exc}')
            self.logger.info(f'Next attempt to get ETA is in {service_query_interval} seconds.')
            time.sleep(service_query_interval)

    @abstractmethod
    def get_control_dict(self) -> Dict[str, Any]:
        """
        Get a dict which contains an info for querying Curlbus service
        Control dict fields:
        - "station_id" (mandatory) is a number that represents the bus station ID (can be found using Google maps)
        - "lines" (optional) is a list of lines user is interested to get ETAs, if empty or not provided all lines ETAs
          will be returned
        Example:
            {'station_id': 12345, 'lines': [21, 42]}
        :return: a dict with info for querying Curlbus service
        """
        raise NotImplementedError

    @abstractmethod
    def send_notification(self):
        """
        Send a notification with bus ETAs
        """
        raise NotImplementedError
