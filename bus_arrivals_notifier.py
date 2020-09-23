#
# Written by denpy in 2020.
# https://github.com/denpy
#
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from timeit import default_timer
from typing import Any, Dict, List, Union
from urllib.parse import urljoin

import requests
from dateutil import parser, tz
from dateutil.relativedelta import relativedelta
from retry.api import retry_call

# Configure a minimal logger
LOG_FORMAT = '%(asctime)s %(name)s:%(lineno)d:%(levelname)s: %(message)s'
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class BusArrivalsNotifier(ABC):
    """
    Live bus arrivals notifier abstract class, for notifying about buses arrivals for a chosen stations
    """

    CURLBUS_BASE_URL = 'https://curlbus.app/'
    SECONDS_IN_MINUTE = 60
    MIN_SERVICE_QUERY_INTERVAL = SECONDS_IN_MINUTE // 6  # 10 seconds, there is no point querying the service more often

    def __init__(self, logger=logger):
        self.logger = logger
        self.arrivals = None

    def _get_station_info(self, station_id: int) -> Dict[str, Any]:
        # Get the data from Curlbus service
        url = urljoin(self.CURLBUS_BASE_URL, str(station_id))
        res = requests.get(url, headers=dict(Accept='application/json'), timeout=3)

        # Handle internal server error
        if res.status_code == 500:
            return dict(errors='Curlbus service got an error')

        return res.json()

    def _make_arrivals_object(
            self,
            station_info_obj: Dict[str, Any],
            query_params_obj: Dict[str, Union[int, List[int]]]):

        # Holds an info about the bus station and bus arrivals
        arrivals = dict(
            errors=None,
            line_num_2_mins_remained={},
            station_city=None,
            station_name=None,
            timestamp=None)

        errors = station_info_obj['errors']
        if errors is not None:
            arrivals['errors'] = errors
            self.logger.error(f'Curlbus service returned errors: {errors}')
            return arrivals

        # Station details
        arrivals['station_city'] = station_info_obj['stop_info']['address']['city']
        arrivals['station_name'] = station_info_obj['stop_info']['name']['EN']

        # Get line numbers and station ID
        line_numbers = query_params_obj.get('line_numbers')
        station_id = str(query_params_obj['station_id'])

        # Sort the list of station arrivals according to the "line_name" (which is actually a number, but Curlbus calls
        # it as "line_name" - it's a str)
        station_arrivals = sorted(station_info_obj['visits'][station_id], key=lambda info: int(info['line_name']))
        for line_info in station_arrivals:
            arrivals['timestamp'] = line_info['timestamp']
            line_number = int(line_info['line_name'])
            if line_numbers and (line_number not in line_numbers):
                # Skip the current "line_number" since it's not in a list of line numbers we interested in
                continue

            # Calculate how many minutes remained from now until the bus will arrive to the station
            mins_until_bus_arrives = relativedelta(parser.parse(line_info['eta']), datetime.now(tz.tzlocal())).minutes

            # Sometimes amount of minutes remained until bus arrives maybe a negative number or 0 in this case it
            # usually means that the bus has arrived to the station or just has left
            mins_until_bus_arrives = 0 if mins_until_bus_arrives <= 0 else mins_until_bus_arrives

            # Check maybe we already have saved how many minutes remained for this line, if we already have let's append
            # the current one. We do so because Curlbus does not aggregate ETAs and returns them as separate fields
            line_num_2_mins_remained = arrivals['line_num_2_mins_remained']
            if line_number in line_num_2_mins_remained:
                mins_remained = line_num_2_mins_remained[line_number]
                mins_remained.append(mins_until_bus_arrives)

                # Remove duplicates and sort
                line_num_2_mins_remained[line_number] = sorted(list(set(mins_remained)))
                continue

            line_num_2_mins_remained[line_number] = [mins_until_bus_arrives]

        return arrivals

    def _notify(self):
        # Get needed parameters for querying Curlbus
        query_params_obj = self.get_query_params_obj()

        # Validate "station_id" field
        station_id = query_params_obj.get('station_id')
        if not isinstance(station_id, int):
            err_msg = 'Missing "station_id"'
            self.logger.error(err_msg)
            raise ValueError(err_msg)

        # Get the station data (errors, etas etc.) from the Curlbus service
        station_info_obj = self._get_station_info(station_id)

        # Normalize station info
        self.arrivals = self._make_arrivals_object(station_info_obj, query_params_obj)
        self.send_notification()

    def run(self, service_query_interval=MIN_SERVICE_QUERY_INTERVAL):
        query_interval = max(service_query_interval, self.MIN_SERVICE_QUERY_INTERVAL)
        attempts = 0
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
                logger.info(f'Querying Curlbus service, attempt #{attempts}')
                attempts += 1

            elapsed = round(default_timer() - start)
            if query_interval < elapsed:
                # If we got here it means that to get the data and send the notification took longer than service
                # query interval, in such case we should not sleep
                logger.warning(f'It took {elapsed} sec to get the data and sent the notification, will not sleep.')
                continue

            if service_query_interval == 0:
                break

            # Calculate how long we should wait until the next attempt to get arrivals
            sleep_period = service_query_interval - elapsed
            self.logger.info(f'Next attempt to get arrivals is in {sleep_period} seconds.')
            time.sleep(sleep_period)

    @abstractmethod
    def get_query_params_obj(self) -> Dict[str, Any]:
        """
        Get a dict which contains an parameters for querying Curlbus service
        Fields:
        - "station_id" (mandatory) is a number that represents a bus station ID (can be found using Google maps)
        - "line_numbers" (optional) is a list of line numbers, if empty or not provided all lines arrivals will be
        returned
        Example:
            {'station_id': 12345, 'line_numbers': [21, 42]}
        :return: a dict with info for querying Curlbus service
        """
        raise NotImplementedError

    @abstractmethod
    def send_notification(self):
        """
        Send a notification with bus arrivals info stored in "self.arrivals" attribute
        Example of "self.arrivals" value:
            {'errors': None,
             'line_num_2_mins_remained': {1: [11, 23], 2: [16]},
             'station_city': 'Tel Aviv',
             'station_name': 'Example Station',
             'timestamp': '2020-06-17 04:36:44+03:00'}
        """
        raise NotImplementedError
