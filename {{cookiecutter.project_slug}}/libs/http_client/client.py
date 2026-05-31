from collections.abc import Mapping
from collections.abc import Sequence
from contextlib import contextmanager
from enum import Enum
from typing import Any
from typing import TypedDict
from urllib.parse import urljoin

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException
from requests.exceptions import Timeout
from urllib3.util.retry import Retry

from .errors import ClientConnectionError
from .errors import ClientRequestError
from .errors import ClientResponseError
from .errors import ClientTimeoutError


class RequestConfig(TypedDict, total=False):
    timeout: float
    verify_ssl: bool
    max_retries: int
    backoff_factor: float
    status_forcelist: Sequence[int]
    allowed_methods: Sequence[str]


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

    @classmethod
    def values(cls) -> set[str]:
        return {method.value for method in cls}


class HTTPClient:
    DEFAULT_TIMEOUT = 30.0
    MIN_TIMEOUT = 1.0
    DEFAULT_CONFIG = {
        "timeout": DEFAULT_TIMEOUT,
        "verify_ssl": True,
        "max_retries": 3,
        "backoff_factor": 0.5,
        "status_forcelist": (429, 500, 502, 503, 504),
        "allowed_methods": tuple(sorted(HTTPMethod.values())),
    }

    def __init__(
        self,
        host: str,
        retry: int | None = None,
        config: RequestConfig | None = None,
    ) -> None:
        if not host:
            error_msg = "Host URL cannot be empty"
            raise ValueError(error_msg)

        self.host = host
        self.config = self._validate_config({**self.DEFAULT_CONFIG, **(config or {})})

        if retry is not None:
            self.config["max_retries"] = max(retry, 0)

        self.session = self._create_session()

    def _validate_config(self, config: RequestConfig) -> RequestConfig:
        if config["timeout"] < self.MIN_TIMEOUT:
            error_msg = f"Timeout must be at least {self.MIN_TIMEOUT} seconds"
            raise ValueError(error_msg)
        if config["max_retries"] < 0:
            error_msg = "Max retries cannot be negative"
            raise ValueError(error_msg)
        if not isinstance(config["verify_ssl"], bool):
            error_msg = "verify_ssl must be a boolean"
            raise ValueError(error_msg)
        if config["backoff_factor"] < 0:
            error_msg = "backoff_factor cannot be negative"
            raise ValueError(error_msg)
        status_list = tuple(int(code) for code in config["status_forcelist"])
        if not status_list:
            error_msg = "status_forcelist cannot be empty"
            raise ValueError(error_msg)
        methods = tuple(method.upper() for method in config["allowed_methods"])
        if not methods:
            error_msg = "allowed_methods cannot be empty"
            raise ValueError(error_msg)
        config["status_forcelist"] = status_list
        config["allowed_methods"] = methods
        return config

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=self._build_retry())
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _build_retry(self) -> Retry:
        return Retry(
            total=self.config["max_retries"],
            backoff_factor=self.config["backoff_factor"],
            status_forcelist=self.config["status_forcelist"],
            allowed_methods=set(self.config["allowed_methods"]),
            respect_retry_after_header=True,
        )

    def __enter__(self) -> "HTTPClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        session = getattr(self, "session", None)
        if session is None:
            return
        session.close()
        self.session = None

    def __del__(self) -> None:
        self.close()

    @contextmanager
    def _handle_request_errors(self):
        try:
            yield
        except Timeout as e:
            logger.error(f"Request timeout: {e!s}")
            error_msg = str(e)
            raise ClientTimeoutError(error_msg) from e
        except RequestsConnectionError as e:
            logger.error(f"Connection error: {e!s}")
            error_msg = str(e)
            raise ClientConnectionError(error_msg) from e
        except requests.HTTPError as e:
            logger.error(f"HTTP error: {e!s}")
            resp = getattr(e, "response", None)
            if resp is not None:
                error_msg = (
                    f"HTTP {resp.status_code}: {getattr(resp, 'reason', '')}, "
                    f"{getattr(resp, 'text', '')}"
                )
            else:
                error_msg = str(e)
            raise ClientResponseError(error_msg, response=resp) from e
        except RequestException as e:
            logger.error(f"Request error: {e!s}")
            error_msg = str(e)
            raise ClientRequestError(error_msg) from e
        except Exception as e:
            logger.exception(f"Unexpected error: {e!s}")
            raise

    def request(  # noqa: PLR0913
        self,
        method: str | HTTPMethod,
        url: str,
        params: Mapping | None = None,
        data: Mapping | None = None,
        json: Mapping | None = None,
        headers: Mapping | None = None,
        timeout: float | None = None,
        verify: bool | None = None,
        extra_kwargs: Mapping[str, Any] | None = None,
    ) -> requests.Response:
        if isinstance(method, str):
            method = method.upper()
            if method not in HTTPMethod.values():
                valid_methods = ", ".join(sorted(HTTPMethod.values()))
                error_msg = f"method must be one of: {valid_methods}"
                raise ValueError(error_msg)
        elif not isinstance(method, HTTPMethod):
            error_msg = "method must be a string or HTTPMethod enum"
            raise TypeError(error_msg)

        full_url = urljoin(self.host, url.lstrip("/"))

        request_kwargs: dict[str, Any] = {
            "headers": headers or {},
            "timeout": timeout if timeout is not None else self.config["timeout"],
            "verify": verify if verify is not None else self.config["verify_ssl"],
            "params": params,
        }
        if extra_kwargs:
            request_kwargs.update(extra_kwargs)

        if data is not None and json is not None:
            error_msg = "cannot provide both data and json"
            raise ValueError(error_msg)
        if data is not None:
            request_kwargs["data"] = data
        if json is not None:
            request_kwargs["json"] = json

        with self._handle_request_errors():
            http_method = method.value if isinstance(method, HTTPMethod) else method
            response = self.session.request(
                method=http_method, url=full_url, **request_kwargs
            )
            response.raise_for_status()
            return response
