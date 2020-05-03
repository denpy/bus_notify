A simple abstract class for querying https://curlbus.app service periodically.  

#### Installation:
1. Clone this repository.
2. Create a new virtual environment and activate it.
3. Run `pip install -r bus_notify/requirments.txt`
4. Implement needed methods as described below.

#### Mandatory methods to implement:
In order to make this work you have to implement two methods:
- `get_service_query_obj` method has to return a needed query parameter for Curlbus service as dictionary.

    - Returned object may include two fields:
        
        - `station_id` is a mandatory field and its value is an integer that represent a bus station ID. 
        - `line_numbers` is an optional field and its value is a list that contains line numbers (integers). If the
         field is not provided or the list is empty information about all lines will be returned otherwise only for
          lines in the list.

- `send_notification` method implements a notification functionality.
 
 Example:
```python
from bus_eta_notifier import BusEtaNotifier


class TestNotifier(BusEtaNotifier):
    def get_service_query_obj(self):
        return {'station_id': 33326, 'line_numbers': [74, 174]}

    def send_notification(self):
        print(self.etas)


if __name__ == '__main__':
    notifier = TestNotifier()
    notifier.run(service_query_interval=10)

```

The query result will be stored in the `etas` property of the class and can be used in the `send_notification` method.

`etas` is a list that contains ETA objects.

Example of the `etas` property content:
```
[{'errors': None,
  'etas': [5],
  'line_number': 21,
  'stattion_name': 'Herzl/Sokolov'}]
```

ETA object fields:

`errors` a list of error messages or `None`.

`etas` a list of integers where each integer represent a number of minutes remained until the bus arrives to the
 station.
 
`line_number` a line (bus) number.

`station_name`  a string that contains the name of the station.