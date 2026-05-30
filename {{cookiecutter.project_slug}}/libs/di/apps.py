import importlib
import inspect

from django.apps import AppConfig, apps
from dependency_injector.containers import DeclarativeContainer


class DIConfig(AppConfig):
    name = "libs.di"

    def ready(self) -> None:
        all_containers: dict[str, list[type[DeclarativeContainer]]] = {}
        requires_map: dict[str, list[type[DeclarativeContainer]]] = {}

        for app_config in apps.get_app_configs():
            try:
                mod = importlib.import_module(f"{app_config.name}.di_containers")
            except ImportError:
                continue

            containers: list[type[DeclarativeContainer]] = []
            for _, cls in inspect.getmembers(mod, inspect.isclass):
                if (
                    issubclass(cls, DeclarativeContainer)
                    and cls is not DeclarativeContainer
                ):
                    containers.append(cls)
            if containers:
                all_containers[app_config.name] = containers

            required = getattr(mod, "requires_containers", [])
            if required:
                requires_map[app_config.name] = required

        for app_name, container_list in all_containers.items():
            pkg = importlib.import_module(app_name)
            for container_cls in container_list:
                container_cls.wire(packages=[pkg])

        for consumer_app, required_containers in requires_map.items():
            consumer_pkg = importlib.import_module(consumer_app)
            for container_cls in required_containers:
                container_cls.wire(packages=[consumer_pkg])
