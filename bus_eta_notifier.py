#
# Copyright 2020. All rights reserved.
#
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from timeit import default_timer
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from dateutil import parser, tz
from dateutil.relativedelta import relativedelta
from retry.api import retry_call

# Configure a minimal logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s:%(levelname)s: %(message)s')


class BusEtaNotifier(ABC):
    """
    A bus estimated time of arrival (ETA) notifier abstract class, for notifying about buses ETAs
    """

    CURLBUS_BASE_URL = 'http://curlbus.app/'
    SECONDS_IN_MINUTE = 60
    MIN_SERVICE_QUERY_INTERVAL = SECONDS_IN_MINUTE // 6  # 10 seconds

    # noinspection PyShadowingNames
    def __init__(self, logger=logger):
        self.logger = logger
        self.etas = []
        self.service_query_interval = None

    def _query_curlbus(self, station_id: int, line_numbers: Optional[List[int]] = None):
        # Clear `etas` list, so we'll not have items from the previous query
        self.etas.clear()

        # Get the data from Curlbus
        station_id = str(station_id)
        url = urljoin(self.CURLBUS_BASE_URL, station_id)
        res = requests.get(url, headers={'Accept': 'application/json'}, timeout=60)
        res_json = res.json()

        errors = res_json['errors']
        if errors is not None and 'visits' not in res_json:
            self.logger.error(f'Curlbus service returned errors: {errors}')
            raise Exception(errors)

        lines_info = res_json['visits'][station_id]
        for line_info in lines_info:
            eta_obj = dict(
                errors=errors,
                stattion_name=res_json['stop_info']['name']['EN'],
                timestamp=line_info['timestamp'])
            line_number = int(line_info['line_name'])  # Curlbus calls the line number as "line_name" (str type)
            eta_obj['line_number'] = line_number
            if line_numbers and line_number not in line_numbers:
                # Skip the current `line_number` since it's not in a list of line numbers we interested in
                continue

            # Calculate how many minutes remained from now until the bus will arrive to the station
            minutes_remained = relativedelta(parser.parse(line_info['eta']), datetime.now(tz.tzlocal())).minutes

            # Sometimes amount of minutes remained maybe a negative number i.e. we calculated `minutes_remained`
            # after the actual ETA, in this case we skip this ETA
            if minutes_remained < 0:
                continue

            # Check maybe we already have an ETA for this line
            is_line_number_in_etas = False
            for eta in self.etas:
                if line_number != eta['line_number']:
                    continue

                # We already have ETA for this line, let's append an another one to it
                etas = eta['etas']
                etas.append(minutes_remained)
                eta['etas'] = list(set(etas))
                is_line_number_in_etas = True
                break

            if not is_line_number_in_etas:
                eta_obj['etas'] = [minutes_remained]
                self.etas.append(eta_obj)

    def _notify(self):
        service_query_obj = self.get_service_query_obj()

        # Validate "station_id" field
        station_id = service_query_obj.get('station_id')
        if not (station_id is not None and isinstance(station_id, int)):
            err_msg = '"station_id" field value must be an integer'
            self.logger.error(err_msg)
            raise ValueError(err_msg)

        self._query_curlbus(station_id, service_query_obj.get('line_numbers'))
        self.send_notification()

    def run(self, service_query_interval=MIN_SERVICE_QUERY_INTERVAL):
        self.service_query_interval = max(service_query_interval, self.MIN_SERVICE_QUERY_INTERVAL)
        while True:
            start = default_timer()
            try:
                retry_call(
                    self._notify,
                    tries=60,
                    delay=1,
                    max_delay=2 * self.SECONDS_IN_MINUTE,
                    logger=self.logger)
            except Exception as exc:
                self.logger.error(f'Failed to get data from Curlbus service. Reason: {exc}')

            elapsed = round(default_timer() - start)
            if self.service_query_interval < elapsed:
                # If we got here i.e. it took longer than service query interval to get the data and send the
                # notification, in such case we should not sleep
                logger.warning(f'It took {elapsed} sec to get the data and sent the notification, will not sleep.')
                continue

            # Calculate how long we should wait until next the next attempt to get ETAs
            sleep_period = self.service_query_interval - elapsed
            self.logger.info(f'Next attempt to get ETA is in {sleep_period} seconds.')
            time.sleep(sleep_period)

    @abstractmethod
    def get_service_query_obj(self) -> Dict[str, Any]:
        """
        Get a dict which contains an info for querying Curlbus service
        Control dict fields:
        - "station_id" (mandatory) is a number that represents a bus station ID (can be found using Google maps)
        - "line_numbers" (optional) is a list of line numbers, if empty or not provided all lines ETAs will be
        returned
        Example:
            {'station_id': 12345, 'line_numbers': [21, 42]}
        :return: a dict with info for querying Curlbus service
        """
        raise NotImplementedError

    @abstractmethod
    def send_notification(self):
        """
        Send a notification with bus ETAs
        """
        raise NotImplementedError
