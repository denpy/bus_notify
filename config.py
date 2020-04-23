import os
import tempfile

from local_config import PUSHOVER_TOKEN, PUSHOVER_USER

# FOO: why do we need this file what so ever? Maybe we need only the local config

assert PUSHOVER_TOKEN, PUSHOVER_USER

# Bus stops IDs and line numbers
HOME_BUS_STOP_ID = '33326'
WORK_BUS_STOP_ID = '25141'
BUS_LINE_NAMES = ['74', '174']  # FOO numbers or names? it actually strings and not ints

# Days FOO - maybe it should be kind of mapping, user provides day names an we map it to corresponding numbers
MON = 0
TUE = 1
WED = 2
THU = 3
FRI = 4
SAT = 5
SUN = 6
MIDWEEK_DAYS = (0, 1, 2, 3, 6)  # Mon, Tue, Wed, Thu, Sun
WEEK_DAYS_2_SKIP = (4, 5)

# URLs
CONTROL_FILE_URL = f'https://dl.dropboxusercontent.com/s/z3pd6zuyl5ckwy1/{CONTROL_FILE_BASENAME}'
NOTIFICATION_URL = f'https://api.pushover.net/1/messages.json?token={PUSHOVER_TOKEN}&user={PUSHOVER_USER}'

# Control file
CONTROL_FILE_BASENAME = 'control.json'
CONTROL_JSON_PATH = os.path.join(tempfile.gettempdir(), CONTROL_FILE_BASENAME)