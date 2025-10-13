from unittest import mock

import pytest
import requests
import responses
from django.test import TestCase
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException
from requests.exceptions import Timeout

from libs.http_client import HTTPClient
from libs.http_client import HTTPMethod
from libs.http_client.exceptions import ClientConnectionError
from libs.http_client.exceptions import ClientRequestError
from libs.http_client.exceptions import ClientResponseError
from libs.http_client.exceptions import ClientTimeoutError


class HTTPClientTest(TestCase):
    def setUp(self):
        """Set up test fixtures before each test"""
        self.host = "https://api.example.com"
        self.client = HTTPClient(host=self.host)

    def tearDown(self):
        """Clean up after each test"""
        self.client.close()

    def test_init_with_invalid_host(self):
        """Test initializing client with invalid host"""
        with pytest.raises(ValueError, match="Host URL cannot be empty"):
            HTTPClient(host="")

    def test_init_with_invalid_timeout(self):
        """Test initializing client with invalid timeout value"""
        with pytest.raises(ValueError, match="Timeout must be at least 1.0 seconds"):
            HTTPClient(host=self.host, config={"timeout": 0.5})

    def test_init_with_valid_config(self):
        """Test initializing client with valid configuration"""
        config = {"timeout": 60, "verify_ssl": False, "max_retries": 5}
        client = HTTPClient(host=self.host, config=config)

        assert client.config["timeout"] == 60
        assert client.config["verify_ssl"] is False
        assert client.config["max_retries"] == 5

    def test_init_with_retry_param(self):
        """Test initializing client with retry parameter"""
        client = HTTPClient(host=self.host, retry=10)
        assert client.config["max_retries"] == 10

        client = HTTPClient(host=self.host, retry=0)
        assert client.config["max_retries"] == 0

        client = HTTPClient(host=self.host, retry=-5)
        assert client.config["max_retries"] == 0

    @responses.activate
    def test_request_with_get_method(self):
        """Test GET request method"""
        responses.add(responses.GET, f"{self.host}/users", json={"id": 1, "name": "John"}, status=200)

        response = self.client.request(HTTPMethod.GET, "/users")

        assert response.status_code == 200
        assert response.json() == {"id": 1, "name": "John"}

    @responses.activate
    def test_request_with_post_method(self):
        """Test POST request method"""
        responses.add(responses.POST, f"{self.host}/users", json={"id": 2, "name": "Smith"}, status=201)

        response = self.client.request(HTTPMethod.POST, "/users", json={"name": "Smith"})

        assert response.status_code == 201
        assert response.json() == {"id": 2, "name": "Smith"}

    @responses.activate
    def test_request_with_put_method(self):
        """Test PUT request method"""
        responses.add(responses.PUT, f"{self.host}/users/1", json={"id": 1, "name": "John Updated"}, status=200)

        response = self.client.request(HTTPMethod.PUT, "/users/1", json={"name": "John Updated"})

        assert response.status_code == 200
        assert response.json() == {"id": 1, "name": "John Updated"}

    @responses.activate
    def test_request_with_delete_method(self):
        """Test DELETE request method"""
        responses.add(responses.DELETE, f"{self.host}/users/1", status=204)

        response = self.client.request(HTTPMethod.DELETE, "/users/1")

        assert response.status_code == 204

    @responses.activate
    def test_request_with_query_params(self):
        """Test request with query parameters"""
        responses.add(
            responses.GET,
            f"{self.host}/users",
            json=[{"id": 1, "name": "John"}],
            status=200,
            match=[responses.matchers.query_param_matcher({"role": "admin"})],
        )

        response = self.client.request(HTTPMethod.GET, "/users", params={"role": "admin"})

        assert response.status_code == 200
        assert response.json() == [{"id": 1, "name": "John"}]

    @mock.patch("requests.Session.request")
    def test_request_timeout_error(self, mock_request):
        """Test request timeout error handling"""
        mock_request.side_effect = Timeout("Request timeout")

        with pytest.raises(ClientTimeoutError):
            self.client.request(HTTPMethod.GET, "/users")

    @mock.patch("requests.Session.request")
    def test_request_connection_error(self, mock_request):
        """Test connection error handling"""
        mock_request.side_effect = RequestsConnectionError("Connection failed")

        with pytest.raises(ClientConnectionError):
            self.client.request(HTTPMethod.GET, "/users")

    @responses.activate
    def test_http_error_handling(self):
        """Test HTTP error handling"""
        responses.add(responses.GET, f"{self.host}/not-found", json={"error": "Resource not found"}, status=404)

        with pytest.raises(ClientResponseError) as exc_info:
            self.client.request(HTTPMethod.GET, "/not-found")

        assert "404" in str(exc_info.value)

    @mock.patch("requests.Session.close")
    def test_with_context_manager(self, mock_close):
        """Test using context manager"""
        with HTTPClient(host=self.host) as client:
            assert isinstance(client, HTTPClient)
            assert hasattr(client, "session")

        # Verify that the close method was called when exiting context manager
        mock_close.assert_called_once()

    def test_request_with_both_data_and_json_should_error(self):
        """Providing both data and json should raise ValueError"""
        with pytest.raises(ValueError, match="cannot provide both data and json"):
            self.client.request(HTTPMethod.POST, "/users", data={"a": 1}, json={"b": 2})

    def test_method_invalid_type_raises_type_error(self):
        """Non-string and non-HTTPMethod should raise TypeError"""
        with pytest.raises(TypeError, match="method must be a string or HTTPMethod enum"):
            self.client.request(123, "/users")

    @responses.activate
    def test_lowercase_method_string_should_work(self):
        """Lowercase method string should be normalized"""
        responses.add(responses.GET, f"{self.host}/users", json={"ok": True}, status=200)
        resp = self.client.request("get", "/users")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    @mock.patch("requests.Session.request")
    def test_request_exception_fallback(self, mock_request):
        """Unhandled RequestException should be wrapped as ClientRequestError"""
        mock_request.side_effect = RequestException("boom")
        with pytest.raises(ClientRequestError):
            self.client.request(HTTPMethod.GET, "/users")

    @mock.patch("requests.Session.request")
    def test_http_error_without_response(self, mock_request):
        """HTTPError without response should still be wrapped safely"""
        mock_request.side_effect = requests.HTTPError("boom")
        with pytest.raises(ClientResponseError):
            self.client.request(HTTPMethod.GET, "/users")

    @responses.activate
    def test_headers_pass_through(self):
        """Custom headers should be sent with the request"""
        expected_headers = {"X-Token": "abc"}
        responses.add(
            responses.GET,
            f"{self.host}/users",
            json={"ok": True},
            status=200,
            match=[responses.matchers.header_matcher(expected_headers)],
        )
        resp = self.client.request(HTTPMethod.GET, "/users", headers=expected_headers)
        assert resp.status_code == 200

    def test_verify_ssl_type_validation(self):
        """verify_ssl must be boolean"""
        with pytest.raises(ValueError, match="verify_ssl must be a boolean"):
            HTTPClient(host=self.host, config={"verify_ssl": "no"})

    @mock.patch("requests.Session.request")
    def test_verify_ssl_propagation(self, mock_request):
        """verify parameter should follow verify_ssl config"""
        client = HTTPClient(host=self.host, config={"verify_ssl": False})
        mock_request.return_value = mock.Mock(status_code=200)
        mock_request.return_value.raise_for_status.return_value = None
        client.request(HTTPMethod.GET, "/users")
        _, kwargs = mock_request.call_args
        assert kwargs["verify"] is False
        client.close()

    @responses.activate
    def test_url_join_with_trailing_slash(self):
        """Host trailing slash should not break URL join"""
        client = HTTPClient(host=f"{self.host}/")
        responses.add(responses.GET, f"{self.host}/users", json={"ok": True}, status=200)
        resp = client.request(HTTPMethod.GET, "/users")
        assert resp.status_code == 200
        client.close()
