import argparse
import sys
from functools import wraps


def arg(*name_or_flags, **kwargs):
    def decorator(func):
        configs = getattr(func, "__script_arg_configs__", [])
        configs.append((name_or_flags, kwargs))
        func.__script_arg_configs__ = configs
        return func

    return decorator


def script_args(func):
    configs = getattr(func, "__script_arg_configs__", None)

    if configs is None:
        return func

    @wraps(func)
    def wrapper(*args):
        parser = argparse.ArgumentParser(description=func.__doc__)
        for flags, kw in configs:
            parser.add_argument(*flags, **kw)

        try:
            parsed = parser.parse_args(args)
        except SystemExit:
            return

        return func(**vars(parsed))

    return wrapper
