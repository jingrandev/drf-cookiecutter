#!/usr/bin/env python
import os
import shutil
import subprocess
import sys

FEATURE_REGISTRY = {
    "redis": {
        "dirs": ["libs/cache"],
        "files": [],
    },
    "celery": {
        "dirs": ["libs/mq", "compose/local/django/celery"],
        "files": ["config/celery.py"],
    },
    "email": {
        "dirs": ["libs/email"],
        "files": [],
    },
    "command": {
        "dirs": ["core/command"],
        "files": [],
    },
}

CONDITIONAL_FILES = {
    "tasks.py": {
        "file": "libs/email/tasks.py",
        "requires": {"celery": "yes", "email": "yes"},
    },
    "celery_signals.py": {
        "file": "libs/logging/celery_signals.py",
        "requires": {"celery": "yes"},
    },
}

FEATURE_FLAGS = {
    "redis": "{{ cookiecutter.use_redis }}",
    "celery": "{{ cookiecutter.use_celery }}",
    "email": "{{ cookiecutter.use_email }}",
    "command": "{{ cookiecutter.use_command }}",
}

# Get the absolute path of the current project directory
PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)


def cleanup_disabled_features(project_directory):
    for feature_name, flag in FEATURE_FLAGS.items():
        if flag == "yes":
            continue
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

    for entry in CONDITIONAL_FILES.values():
        requirements = entry["requires"]
        for req_feature, req_value in requirements.items():
            flag = FEATURE_FLAGS.get(req_feature, "no")
            if flag != req_value:
                path = os.path.join(project_directory, entry["file"])
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Removed conditional file: {path}")
                break


def run_command(command, cwd=None):
    """Run command and check result"""
    print(f"Executing command: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd or PROJECT_DIRECTORY)
    if result.returncode != 0:
        print(f"Command failed: {command}")
        sys.exit(result.returncode)


def process_license_files():
    """Process license files based on selected license"""
    license_type = "{{ cookiecutter.open_source_license }}"

    # If not open source, remove the LICENSE file
    if license_type == "Not open source":
        license_file = os.path.join(PROJECT_DIRECTORY, "LICENSE")
        if os.path.exists(license_file):
            os.remove(license_file)
            print("Removed LICENSE file as project is not open source")
    elif license_type == "GPLv3":
        # For GPLv3, rename LICENSE to COPYING (GNU standard)
        license_file = os.path.join(PROJECT_DIRECTORY, "LICENSE")
        copying_file = os.path.join(PROJECT_DIRECTORY, "COPYING")
        if os.path.exists(license_file):
            os.rename(license_file, copying_file)
            print("Renamed LICENSE to COPYING for GPLv3 license (GNU standard)")
    elif license_type == "Apache Software License 2.0":
        # For Apache, create an empty NOTICE file
        notice_file = os.path.join(PROJECT_DIRECTORY, "NOTICE")
        with open(notice_file, "w") as f:
            f.write("# NOTICE file for Apache License 2.0\n\n")
            f.write("This product includes software developed by\n")
            f.write("{{ cookiecutter.author_name }} <{{ cookiecutter.email }}>\n")
        print("Created NOTICE file for Apache License 2.0")
    else:
        # MIT or BSD license - standard LICENSE file is fine
        print(f"License file created with {license_type} license")


def remove_license_files():
    """Remove license files that are not needed for the selected license"""
    license_type = "{{ cookiecutter.open_source_license }}"

    # Remove COPYING file if not GPLv3
    if license_type != "GPLv3":
        copying_file = os.path.join(PROJECT_DIRECTORY, "COPYING")
        if os.path.exists(copying_file):
            os.remove(copying_file)

    # Remove NOTICE file if not Apache
    if license_type != "Apache Software License 2.0":
        notice_file = os.path.join(PROJECT_DIRECTORY, "NOTICE")
        if os.path.exists(notice_file):
            os.remove(notice_file)


def cleanup_db_artifacts():
    """Remove artifacts for the non-selected database engine"""
    database_engine = "{{ cookiecutter.database_engine }}"
    cleanup_map = {
        "mysql": [
            os.path.join(PROJECT_DIRECTORY, ".envs", ".postgres"),
            os.path.join(PROJECT_DIRECTORY, "compose", "production", "postgres"),
        ],
        "postgres": [
            os.path.join(PROJECT_DIRECTORY, ".envs", ".mysql"),
            os.path.join(PROJECT_DIRECTORY, "compose", "production", "mysql"),
        ],
    }
    for target in cleanup_map.get(database_engine, []):
        if os.path.isdir(target):
            shutil.rmtree(target)
            print(f"Removed directory: {target}")
        elif os.path.exists(target):
            os.remove(target)
            print(f"Removed file: {target}")


def generate_requirements_files():
    """Generate requirements files using uv"""
    # Create requirements directory if it doesn't exist
    requirements_dir = os.path.join(PROJECT_DIRECTORY, "requirements")
    if not os.path.exists(requirements_dir):
        os.makedirs(requirements_dir)
        print(f"Created requirements directory at {requirements_dir}")

    # Generate base.txt
    print("Generating base requirements file...")
    run_command("uv export --no-hashes --no-header --output-file requirements/base.txt --no-group dev --no-group prod")

    # Generate develop.txt
    print("Generating development requirements file...")
    run_command("uv export --no-hashes --no-header --output-file requirements/develop.txt --group dev")

    # Generate production.txt
    print("Generating production requirements file...")
    run_command("uv export --no-hashes --no-header --output-file requirements/production.txt --group prod")

    print("Requirements files generated successfully")


def init_git_repo():
    """Initialize Git repository"""
    if not os.path.exists(os.path.join(PROJECT_DIRECTORY, ".git")):
        run_command("git init")
        print("Initialized Git repository")


def setup_pre_commit():
    """Set up pre-commit hooks if pre-commit is available"""
    try:
        # Check if pre-commit is available
        result = subprocess.run(["which", "pre-commit"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Setting up pre-commit hooks...")
            run_command("pre-commit install")
            print("Pre-commit hooks installed successfully")
    except Exception as e:
        print(f"Note: pre-commit not installed or error occurred: {e}")
        print("You can manually install pre-commit hooks later with 'pre-commit install'")


def main():
    """Main function to execute all initialization steps"""
    print("Starting post-project initialization script...")

    # Process license files
    process_license_files()

    # Remove unnecessary license files
    remove_license_files()

    # Cleanup non-selected database artifacts
    cleanup_db_artifacts()

    cleanup_disabled_features(PROJECT_DIRECTORY)

    generate_requirements_files()

    # Initialize Git repository
    init_git_repo()

    # Set up pre-commit hooks
    setup_pre_commit()

    print("Post-project initialization script completed!")


if __name__ == "__main__":
    main()
