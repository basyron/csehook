from os.path import join as os_join
from pathlib import Path

import requests


CSE_URI = "{YOUR_CSE_URI_HERE}"  # example: https://cse.google.com/cse?cx=...
DEFAULT_DRIVER = os_join(
    Path(__file__).parent.resolve(), "driver/mac/chrome/chromedriver"
)
USER_AGENTS = requests.get(
    "https://raw.githubusercontent.com/tamimibrahim17/"
    "List-of-user-agents/master/Chrome.txt"
).text.split('\n')[3:]

RENEW_CSE_DEFAULT = 38
