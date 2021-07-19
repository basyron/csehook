from os.path import join as os_join
from pathlib import Path

import requests


CSE_URI = "https://cse.google.com/cse?cx=8d57d6f6129439b92"
DEFAULT_DRIVER = os_join(
    Path(__file__).parent.resolve(), "driver/mac/chrome/chromedriver"
)
USER_AGENTS = requests.get(
    "https://raw.githubusercontent.com/tamimibrahim17/"
    "List-of-user-agents/master/Chrome.txt"
).text.split('\n')[3:]

RENEW_CSE_DEFAULT = 38
