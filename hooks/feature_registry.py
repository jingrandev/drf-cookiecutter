import os
import shutil

FEATURE_REGISTRY = {
    "redis": {
        "dirs": [
            "libs/cache",
        ],
        "files": [],
    },
    "celery": {
        "dirs": [
            "libs/mq",
        ],
        "files": [],
    },
    "email": {
        "dirs": [
            "libs/email",
        ],
        "files": [],
    },
}

FEATURE_FLAGS = {
    "redis": "{{ cookiecutter.use_redis }}",
    "celery": "{{ cookiecutter.use_celery }}",
    "email": "{{ cookiecutter.use_email }}",
}


def get_disabled_features():
    return [name for name, flag in FEATURE_FLAGS.items() if flag != "yes"]


def get_enabled_features():
    return [name for name, flag in FEATURE_FLAGS.items() if flag == "yes"]


def cleanup_disabled_features(project_directory):
    for feature_name in get_disabled_features():
        config = FEATURE_REGISTRY.get(feature_name)
        if not config:
            continue
        for d in config.get("dirs", []):
            path = os.path.join(project_directory, d)
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"Removed directory: {path}")
        for f in config.get("files", []):
            path = os.path.join(project_directory, f)
            if os.path.exists(path):
                os.remove(path)
                print(f"Removed file: {path}")
