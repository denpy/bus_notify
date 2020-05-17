A simple abstract class for querying https://curlbus.app service periodically.

https://curlbus.app is a service that provides an information about bus times arrivals for Israeli public transport
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
from bus_eta_notifier import BusEtaNotifier


class TestNotifier(BusEtaNotifier):
    
    def __init__(self):
        super(TestNotifier, self).__init__()

    def get_query_params_obj(self):
        return {'station_id': 12345, 'line_numbers': [21, 42]}

    def send_notification(self):
        print(self.etas)


if __name__ == '__main__':
    notifier = TestNotifier()
    notifier.run(service_query_interval=10)

```

The query result will be stored in the `etas` attribute of the class instance and can be used in the `send_notification
` method. 

Example of the `etas` property content:
```
{'errors': None,
 'line_number_2_etas': {42: [0, 6, 12]},
 'station_city': 'Some city',
 'station_name': 'Some station name',
 'timestamp': '2020-05-17 15:45:03+03:00'}
```

ETA object fields:

`errors` is field that contains errors returned by the Curlbus service or `None`.

`line_number_2_etas` is a dict that contains a mapping between line numbers and its ETAs list. Note: `line_number_2_etas
` keys are integers.

`line_number` is an integer that represents a line (bus) number.

`station_name` is a string that contains the name of the station.

`timestamp` is a string that contains the timestamp of the query. The format is "yyyy-mm-dd hh:mm:ss+UTC-Offset"