from dependency_injector import containers
from dependency_injector import providers

from .client import HTTPClient


class HTTPClientContainer(containers.DeclarativeContainer):
    http_client_factory = providers.Factory(HTTPClient)
