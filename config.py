from os.path import join as os_join
from pathlib import Path


DEFAULT_DRIVER = os_join(
    Path(__file__).parent.resolve(), "driver/mac/chrome/chromedriver"
)
