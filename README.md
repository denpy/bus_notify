A repository for the app which sends notifications about bus ETA.

#### Installation:
1. Clone this repository.
2. Create a new virtual environment and activate it.
3. Run `pip install -r bus_notify/requirments.txt`
4. Implement needed methods as described below.

#### Mandatory methods to implement:
In order to make this work you have to implement two methods:
- `get_service_query_obj` has to return a needed query parameter for Curlbus service as dictionary.

    - Returned object may include two fields:
        
        - `station_id` is a mandatory field and its value is an integer that represent a bus station ID. 
        - `lines` is an optional field and its value is a list that contains line numbers (integers). If the field is
         not provided or the list is empty information about all lines will be returned otherwise only for lines in
          the list.

- `send_notification` implements a notification functionality.
 
 Example:
```python
from bus_eta_notifier import BusEtaNotifier


class TestNotifier(BusEtaNotifier):
    def get_service_query_obj(self):
        return {'station_id': 12345, 'lines': [21, 42]}

    def send_notification(self):
        print(self.etas)


if __name__ == '__main__':
    notifier = TestNotifier()
    notifier.run(service_query_interval=10)

```