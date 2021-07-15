from urllib.parse import urlparse

from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver

from config import DEFAULT_DRIVER


class WiredDriver:

    def __init__(self,
                 path: str = DEFAULT_DRIVER,
                 headless: bool = True,
                 proxy: str = str()):

        self._options = Options()
        self._options.headless = headless
        self._seleniumwire_options = {}

        if proxy:
            proxy = urlparse(proxy)
            _host = proxy.hostname
            if proxy.port:
                _host = f"{_host}:{proxy.port}"
            self._seleniumwire_options["proxy"] = {
                "http": f"http://{_host}",
                "https": f"https://{_host}",
                "no_proxy": "localhost,127.0.0.1"
            }

        self.instance = webdriver.Chrome(
            path,
            options=self._options,
            seleniumwire_options=self._seleniumwire_options
        )
