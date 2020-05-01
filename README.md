# bus_notify
A repository for the app which sends notifications about bus ETA.

In order to make this work you have to implement two methods:

- "get_service_query_obj" has to return a need query parameter for Curlbus service (a bus station ID and
 optionally lines numbers) as dictionary.
 - "send_notification" implements a notification functionality.
 
 Example:
```python
from bus_eta_notifier import BusEtaNotifier
from pprint import pprint


class TestNotifier(BusEtaNotifier):
    def get_service_query_obj(self):
        return {'station_id': 12345, 'lines': [21, 42]}

    def send_notification(self):
        pprint(self.etas)


if __name__ == '__main__':
    notifier = TestNotifier()
    notifier.run(service_query_interval=10)
```