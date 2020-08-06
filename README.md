A simple abstract class for querying https://curlbus.app service periodically.

https://curlbus.app is a service that provides an information about bus arrivals for Israeli public transport
service providers.

#### Installation:
1. Clone this repository.
2. Create a new virtual environment and activate it.
3. Run `pip install -r bus_notify/requirments.txt`
4. Implement needed methods as described below.

#### Mandatory methods to implement:
In order to make this work you have to implement two methods:
- `get_query_params_obj` method has to return a needed query parameters for Curlbus service as a dictionary.

    - Returned object may include two fields:
        
        - `station_id` is a mandatory field and its value is an integer that represent a bus station ID. 
        - `line_numbers` is an optional field and its value is a list that contains line numbers (integers). If the
         field is not provided or the list is empty information about all lines will be returned otherwise only for
          lines in the list.

- `send_notification` is method that implements a notification functionality.
 
 Example:
```python
from bus_notify.bus_arrivals_notifier import BusArrivalsNotifier


class TestNotifier(BusArrivalsNotifier):
    
    def __init__(self):
        super(TestNotifier, self).__init__()

    def get_query_params_obj(self):
        return {'station_id': 12345, 'line_numbers': [21, 42]}

    def send_notification(self):
        print(self.arrivals)


if __name__ == '__main__':
    notifier = TestNotifier()
    notifier.run(service_query_interval=20)

```

Note: you can provide the `service_query_interval` parameter to the `run` method, it's amount of seconds to wait
 between Curlbus queries. The default and minimal value us 10 as there is no point to query Curlbus more often, if the
  value is 0 then a single query will be performed.

The query result will be stored in the `arrivals` attribute of the class instance and can be used in the
 `send_notification` method. 

Example of the `arrivals` property content:
```
{'errors': None,
 'line_num_2_mins_remained': {1: [11, 23], 2: [16]},
 'station_city': 'Tel Aviv',
 'station_name': 'Example Station',
 'timestamp': '2020-06-17 04:36:44+03:00'}
```

Arrivals object fields:

`errors` is field that contains errors returned by the Curlbus service or `None`.

`line_num_2_mins_remained` is a dict that contains a mapping between line number and a list which contains values of
 how many minutes remained until the bus arrival.
 Note: `line_number_2_etas` keys are integers.

`station_city` is a string that contains the station city name.

`station_name` is a string that contains the name of the station.

`timestamp` is a string that contains the timestamp of the query. The format is "yyyy-mm-dd hh:mm:ss+UTC-Offset"