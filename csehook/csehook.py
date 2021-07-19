import json
import random
import re
import string
from contextlib import suppress
from http import HTTPStatus
from itertools import chain
from time import sleep
from typing import Any, NewType, Iterator, Union
from urllib.parse import parse_qs, quote, urlparse

import requests

from csehook.utils.wired_driver import WiredDriver
from config import USER_AGENTS


_alphabet = string.ascii_letters
_GoogleCSEJson = NewType("_GoogleCSEJson", dict[str, Any])
_GoogleCSEResults = NewType("_GoogleCSEResults", list[dict[str, Any]])
_GoogleCSEIterator = NewType("_GoogleCSEIterator", Iterator[_GoogleCSEResults])


class CseHook:

    _MAX_PROXY_RETRIES = 50
    _STANDARD_SLEEP = 10
    _TIMEOUT = 8

    def __init__(self,
                 cse_uri: str,
                 wired_driver: WiredDriver,
                 word_size: int = 5):

        self._amount_of_words: int = word_size
        self._word_size: int = word_size

        self._cse_uri = urlparse(cse_uri)
        _is_cse_uri_valid: bool = any([
            self._cse_uri.query.startswith("cx="),
            self._cse_uri.hostname.startswith("cse.google.com")
        ])
        if not _is_cse_uri_valid:
            raise AttributeError("An invalid Google CSE URI was specified.")

        self._wired_driver: WiredDriver = wired_driver
        if not isinstance(self._wired_driver, WiredDriver):
            raise AttributeError("Specify a valid WiredDriver instance.")

        self._cse_api_pattern: str = "https://cse.google.com/cse/element/"
        self._cse_regex = re.compile(
            r"(?<=google[.]search[.]cse[.]api)"
            r"([0-9]*\()"
            r"((.|\n|[{}]|)*)(?=\))"
        )

        self._cse_api_uris: list = []
        self._pages = {
            label: start
            for label, start in zip(range(1, 11), range(0, 91, 10))
        }

        self._proxy_list = self._config_proxy_list()

    def _get_modified_uri(self, uri: str, query: str, page: int = 1) -> str:
        """Parse URL, modify it and return its requestable resource."""
        parsed_uri = urlparse(uri)
        base_uri = (
            f"{parsed_uri.scheme}://{parsed_uri.hostname}{parsed_uri.path}"
        )

        parsed_query = parse_qs(parsed_uri.query)
        parsed_query['q'] = [query]
        if page > 1:
            parsed_query["start"] = [self._pages.get(page)]

        query_string = '&'.join(
            f"{k}={v[0]}" for k, v in parsed_query.items()
        )

        return f"{base_uri}?{query_string}"

    @staticmethod
    def _config_proxy_list() -> list:
        response = requests.get(
            "https://proxylist.geonode.com/api/proxy-list?"
            "limit=100&page=1&sort_by=lastChecked&sort_type=desc"
            "&speed=fast"
        )
        return response.json().get("data")

    def _get_random_words(self) -> Iterator[str]:
        """Yield random words based on word_size and amount_of_words."""
        yield from (
            ''.join(random.choice(_alphabet) for _ in range(self._word_size))
            for _ in range(self._amount_of_words)
        )

    def _config_new_cse_api_uris(self) -> None:
        """Configures new CSE API URIs to be used."""

        self._cse_api_uris = []

        for query in self._get_random_words():
            uri = self._get_modified_uri(self._cse_uri.geturl(), query)

            self._wired_driver.instance.get(uri)
            wired_requests = (
                request.url
                for request in self._wired_driver.instance.requests
            )

            self._cse_api_uris.append(next(filter(
                lambda req: req.startswith(self._cse_api_pattern),
                wired_requests
            )))

            del self._wired_driver.instance.requests

    def _get_response(self,
                      uri: str,
                      headers: dict,
                      proxies: dict,
                      retries: int = 0) -> Union[requests.Response, bool]:
        """Attempt to request with specified params.

        Returns:
            bool -- when a request raised an exception.
            requests.Response -- when endpoint was requested successfully.
        """
        with suppress(Exception):
            response = requests.get(
                uri, headers=headers, proxies=proxies, timeout=self._TIMEOUT
            )
            return response

        if retries >= self._MAX_PROXY_RETRIES:
            self._proxy_list = self._config_proxy_list()

        return False

    def _search_page(self,
                     uri: str,
                     query: str,
                     page: int = 1) -> Union[_GoogleCSEJson, dict]:
        """Request a CSE API and return its json."""

        schemas = ("http", "https")
        error_count = 0
        response = False

        # Retries different proxies until we have a response.
        while not response:
            headers = {"User-Agent": random.choice(USER_AGENTS)}

            if not self._proxy_list:
                self._proxy_list = self._config_proxy_list()

            chosen_proxy = random.choice(self._proxy_list)

            protocol = chosen_proxy.get('protocols')[0]
            ip = chosen_proxy.get("ip")
            port = chosen_proxy.get("port")

            proxies = {k: f"{protocol}://{ip}:{port}" for k in schemas}

            response = self._get_response(
                self._get_modified_uri(uri, query, page),
                headers=headers,
                proxies=proxies,
                retries=error_count
            )
            # Remove bad proxy from list.
            if not response:
                self._proxy_list.pop(self._proxy_list.index(chosen_proxy))

            error_count += 1

            # Avoid too many requests to Geonode.
            # Sometimes proxies are just bad in that moment.
            if error_count > self._MAX_PROXY_RETRIES:
                error_count = 0

        status_code = response.status_code

        if status_code == HTTPStatus.FORBIDDEN:
            return {"error": "temp_ban"}

        api_json = json.loads(self._cse_regex.findall(response.text)[0][1])

        return api_json

    def search(self,
               query: str,
               renew_cse_uris: bool = False) -> _GoogleCSEIterator:
        """Get Google CSE results using our CSE API URIs.

        Return: an iterable object with all available Google CSE pages.
        """

        query = quote(str(query))

        if not self._cse_api_uris or renew_cse_uris:
            self._config_new_cse_api_uris()

        first_page = self._search_page(
            random.choice(self._cse_api_uris), query
        )

        error = first_page.get("error")
        while error:
            # If we were temporarily banned, return False.
            if isinstance(error, str):
                return False

            # If old CSE API URIs start to fail, refresh them.
            sleep(self._STANDARD_SLEEP)
            self._config_new_cse_api_uris()
            first_page = self._search_page(
                random.choice(self._cse_api_uris), query
            )

        first_result = iter((first_page.get("results", []),))

        if len(first_page.get("cursor", {}).get("pages", [])) <= 1:
            return first_result

        # If more then one page available, yield them all on-demand.
        yield from chain(
            first_result, (
                results
                for p in tuple(self._pages.keys())[1:]
                if (
                    results := self._search_page(
                        random.choice(self._cse_api_uris), query, p
                    ).get("results", [])
                )
            )
        )
