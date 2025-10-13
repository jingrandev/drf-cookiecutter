from collections.abc import Mapping
from contextlib import contextmanager
from enum import Enum
from typing import TypedDict
from urllib.parse import urljoin

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException
from requests.exceptions import Timeout

from .exceptions import ClientConnectionError
from .exceptions import ClientRequestError
from .exceptions import ClientResponseError
from .exceptions import ClientTimeoutError


class RequestConfig(TypedDict, total=False):
    """Type hints for request configuration"""

    timeout: float
    verify_ssl: bool
    max_retries: int


class HTTPMethod(str, Enum):
    """HTTP methods supported by the client"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"

    @classmethod
    def values(cls) -> set[str]:
        """Return a set of all supported HTTP methods"""
        return {method.value for method in cls}


class HTTPClient:
    """HTTP client with improved error handling and configuration options.

    This client provides a robust interface for making HTTP requests with:
    - Automatic retry handling
    - Consistent error handling
    - Configurable timeouts and SSL verification
    - Session management

    Usage:
        ```python
        with HTTPClient('https://api.example.com') as client:
            response = client.request('GET', '/users')
        ```
    """

    DEFAULT_TIMEOUT = 30.0  # seconds
    DEFAULT_CONFIG = {"timeout": DEFAULT_TIMEOUT, "verify_ssl": True, "max_retries": 3}
    MIN_TIMEOUT = 1.0  # Minimum allowed timeout in seconds

    def __init__(
        self,
        host: str,
        retry: int | None = None,
        config: RequestConfig | None = None,
    ) -> None:
        """Initialize the HTTP client.

        Args:
            host: Base URL for all requests
            retry: Number of retries for failed requests
            config: Additional configuration options

        Raises:
            ValueError: If configuration values are invalid
        """
        if not host:
            error_msg = "Host URL cannot be empty"
            raise ValueError(error_msg)

        self.host = host.rstrip("/")
        self.config = self._validate_config({**self.DEFAULT_CONFIG, **(config or {})})

        if retry is not None:
            self.config["max_retries"] = max(retry, 0)

        # Create session once during initialization
        self.session = self._create_session()

    def _validate_config(self, config: RequestConfig) -> RequestConfig:
        """Validate configuration values.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validated configuration dictionary

        Raises:
            ValueError: If any configuration values are invalid
        """
        if config["timeout"] < self.MIN_TIMEOUT:
            error_msg = f"Timeout must be at least {self.MIN_TIMEOUT} seconds"
            raise ValueError(error_msg)
        if config["max_retries"] < 0:
            error_msg = "Max retries cannot be negative"
            raise ValueError(error_msg)
        if not isinstance(config["verify_ssl"], bool):
            error_msg = "verify_ssl must be a boolean"
            raise ValueError(error_msg)
        return config

    def _create_session(self) -> requests.Session:
        """Create and configure a new session with retry handling."""
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=self.config["max_retries"])
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def __enter__(self) -> "HTTPClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        """Close the session and free resources."""
        if hasattr(self, "session"):
            self.session.close()

    def __del__(self) -> None:
        """Attempt to clean up if context manager wasn't used."""
        self.close()

    @contextmanager
    def _handle_request_errors(self):
        """Context manager for handling request errors."""
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
                    f"HTTP {resp.status_code}: {getattr(resp, 'reason', '')}, {getattr(resp, 'text', '')}"
                )
            else:
                error_msg = str(e)
            raise ClientResponseError(error_msg) from e
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
    ) -> requests.Response:
        """
        Send HTTP request with improved error handling and configuration

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Request URL path
            params: URL parameters
            data: Form data
            json: JSON data
            headers: Request headers

        Returns:
            Response object

        Raises:
            ClientTimeoutError: Request timeout
            ClientConnectionError: Connection failed
            ClientRequestError: Other request errors
            ClientResponseError: Invalid response
            ValueError: Invalid method
        """
        # Normalize method to HTTPMethod enum
        if isinstance(method, str):
            method = method.upper()
            if method not in HTTPMethod.values():
                valid_methods = ", ".join(sorted(HTTPMethod.values()))
                error_msg = f"method must be one of: {valid_methods}"
                raise ValueError(error_msg)
        elif not isinstance(method, HTTPMethod):
            error_msg = "method must be a string or HTTPMethod enum"
            raise TypeError(error_msg)

        # Build full URL with parameters
        full_url = urljoin(self.host, url.lstrip("/"))

        # Prepare request kwargs
        request_kwargs = {
            "headers": headers or {},
            "timeout": self.config["timeout"],
            "verify": self.config["verify_ssl"],
            "params": params,
        }

        # Handle request body
        if data is not None and json is not None:
            error_msg = "cannot provide both data and json"
            raise ValueError(error_msg)
        if data is not None:
            request_kwargs["data"] = data  # Send as form data
        if json is not None:
            request_kwargs["json"] = json  # Send as JSON

        with self._handle_request_errors():
            # Use session for the request to benefit from retry configuration
            http_method = method.value if isinstance(method, HTTPMethod) else method
            response = self.session.request(method=http_method, url=full_url, **request_kwargs)
            response.raise_for_status()
            return response
