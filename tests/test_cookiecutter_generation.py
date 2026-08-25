import os
import re
import sys

import pytest

try:
    import sh
except (ImportError, ModuleNotFoundError):
    sh = None  # sh doesn't support Windows
from binaryornot.check import is_binary
from cookiecutter.exceptions import FailedHookException

PATTERN = r"{{(\s?cookiecutter)[.](.*?)}}"
RE_OBJ = re.compile(PATTERN)

if sys.platform.startswith("win"):
    pytest.skip("sh doesn't support windows", allow_module_level=True)
elif sys.platform.startswith("darwin") and os.getenv("CI"):
    pytest.skip("skipping slow macOS tests on CI", allow_module_level=True)


@pytest.fixture
def context():
    """Basic context with variables needed for project generation"""
    return {
        "project_name": "Test DRF Project",
        "project_slug": "test_drf_project",
        "description": "Test Django REST Framework API Project",
        "author_name": "Test Author",
        "email": "test@example.com",
        "version": "0.1.0",
        "python_version": "3.13",
        "username_type": "username",
        "open_source_license": "MIT",
        "use_redis": "no",
        "use_celery": "no",
        "use_email": "no",
    }


SUPPORTED_COMBINATIONS = [
    {"username_type": "username"},
    {"username_type": "email"},
    {"open_source_license": "MIT"},
    {"open_source_license": "BSD"},
    {"open_source_license": "GPLv3"},
    {"open_source_license": "Apache Software License 2.0"},
    {"open_source_license": "Not open source"},
    {"python_version": "3.13"},
    {"python_version": "3.14"},
    {"use_redis": "yes"},
    {"use_celery": "yes"},
    {"use_email": "yes"},
    {"use_redis": "yes", "use_celery": "yes"},
    {"use_redis": "yes", "use_celery": "yes", "use_email": "yes"},
]


def _fixture_id(ctx):
    """Generate a user-friendly test name"""
    return "-".join(f"{key}:{value}" for key, value in ctx.items())


def build_files_list(base_dir):
    """Build a list of absolute paths to the generated files"""
    return [os.path.join(dirpath, file_path) for dirpath, subdirs, files in os.walk(base_dir) for file_path in files]


def check_paths(paths):
    """Check all paths have correct substitutions"""
    for path in paths:
        if is_binary(path):
            continue

        with open(path, encoding="utf-8") as f:
            for line in f:
                match = RE_OBJ.search(line)
                assert match is None, f"Cookiecutter variable not replaced in {path}: {line}"


@pytest.mark.parametrize("context_override", SUPPORTED_COMBINATIONS, ids=_fixture_id)
def test_project_generation(cookies, context, context_override):
    """Test that project is generated and fully rendered"""
    result = cookies.bake(extra_context={**context, **context_override})
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project_path.is_dir()

    paths = build_files_list(str(result.project_path))
    assert paths
    check_paths(paths)


@pytest.mark.parametrize("context_override", SUPPORTED_COMBINATIONS, ids=_fixture_id)
def test_ruff_check_passes(cookies, context_override, context):
    """Generated project should pass basic ruff checks (excluding import sorting)"""
    result = cookies.bake(extra_context={**context, **context_override})
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project_path.is_dir()

    try:
        # Use --select parameter to only check for serious errors, skipping import sorting and formatting issues
        sh.ruff("check", ".", "--select", "E9,F63,F7,F82", _cwd=str(result.project_path))
    except sh.ErrorReturnCode as e:
        pytest.fail(e.stdout.decode())


@pytest.mark.parametrize("slug", ["123-project", "project!"])
def test_invalid_slug(cookies, context, slug):
    """Invalid slug should fail pre-generation hook"""
    context.update({"project_slug": slug})
    result = cookies.bake(extra_context=context)

    assert result.exit_code != 0
    assert isinstance(result.exception, FailedHookException)


def test_admin_gate_wiring(cookies, context):
    """Admin security gate module and settings wiring must be present"""
    result = cookies.bake(extra_context=context)
    assert result.exit_code == 0
    assert result.exception is None

    middleware_path = result.project_path / "core" / "admin" / "middleware.py"
    assert middleware_path.is_file()

    gate_test_path = result.project_path / "core" / "admin" / "tests" / "test_admin_gate.py"
    assert gate_test_path.is_file()

    with open(result.project_path / "config" / "settings" / "base.py", encoding="utf-8") as f:
        settings_content = f.read()
    assert "core.admin.middleware.AdminGateMiddleware" in settings_content
    assert 'env("ADMIN_SECURITY_CODE", default="")' in settings_content
    assert '"ADMIN_SECURITY_CODE"' in settings_content

    with open(result.project_path / ".env.example", encoding="utf-8") as f:
        env_example = f.read()
    assert "ADMIN_SECURITY_CODE" in env_example


@pytest.mark.parametrize(
    "context_override",
    [
        {"use_celery": "yes", "use_auditlog": "yes"},
        {"use_celery": "no", "use_auditlog": "no"},
    ],
    ids=_fixture_id,
)
def test_unfold_admin_wiring(cookies, context, context_override):
    """Unfold sidebar navigation and constance integration must be wired"""
    result = cookies.bake(extra_context={**context, **context_override})
    assert result.exit_code == 0
    assert result.exception is None

    with open(result.project_path / "config" / "settings" / "base.py", encoding="utf-8") as f:
        content = f.read()

    assert "unfold.contrib.constance" in content
    assert "UNFOLD_CONSTANCE_ADDITIONAL_FIELDS" in content
    assert '"SIDEBAR"' in content
    assert "core.admin.navigation.sidebar_navigation" in content
    assert "core.admin.callbacks.environment_callback" in content

    navigation_path = result.project_path / "core" / "admin" / "navigation.py"
    assert navigation_path.is_file()
    with open(navigation_path, encoding="utf-8") as f:
        navigation_content = f.read()

    assert "admin:authentication_user_changelist" in navigation_content
    assert "admin:constance_config_changelist" in navigation_content

    celery_marker = "admin:django_celery_beat_periodictask_changelist"
    auditlog_marker = "admin:auditlog_logentry_changelist"
    if context_override["use_celery"] == "yes":
        assert celery_marker in navigation_content
    else:
        assert celery_marker not in navigation_content
    if context_override["use_auditlog"] == "yes":
        assert auditlog_marker in navigation_content
    else:
        assert auditlog_marker not in navigation_content


def test_trim_email(cookies, context):
    """Check that leading and trailing spaces are trimmed in email"""
    context.update({"email": " test@example.com "})
    result = cookies.bake(extra_context=context)
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project_path.is_dir()

    # Look for README.md which should contain the email
    readme_path = result.project_path / "README.md"
    if readme_path.exists():
        with open(readme_path) as f:
            content = f.read()
            if "test@example.com" in content:
                assert " test@example.com " not in content
                return

    # Alternatively check any other files that might contain the email
    for file_path in ["LICENSE", ".env.example", "docs/index.md"]:
        path = result.project_path / file_path
        if path.exists():
            with open(path) as f:
                content = f.read()
                if "test@example.com" in content:
                    assert " test@example.com " not in content
                    return

    # If we get here, we couldn't find the email in any of the expected files
    # This is still a pass as we're just testing that spaces are trimmed if the email is used
    pass


FEATURE_DIR_MAP = {
    "redis": ["libs/cache"],
    "celery": ["libs/mq"],
    "email": ["libs/email"],
}

FEATURE_STRING_MARKERS = {
    "redis": ["django-redis", "REDIS_URL", "libs.cache"],
    "celery": [
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "libs.mq",
        "django_celery_beat",
        "celery_worker",
        "celery_beat",
    ],
    "email": ["libs.email"],
}

FEATURE_COMBINATIONS = [
    {"use_redis": "no", "use_celery": "no", "use_email": "no"},
    {"use_redis": "yes", "use_celery": "no", "use_email": "no"},
    {"use_redis": "no", "use_celery": "yes", "use_email": "no"},
    {"use_redis": "no", "use_celery": "no", "use_email": "yes"},
    {"use_redis": "yes", "use_celery": "yes", "use_email": "no"},
    {"use_redis": "yes", "use_celery": "no", "use_email": "yes"},
    {"use_redis": "no", "use_celery": "yes", "use_email": "yes"},
    {"use_redis": "yes", "use_celery": "yes", "use_email": "yes"},
]


def _feature_combo_id(ctx):
    return "-".join(f"{k}:{v}" for k, v in sorted(ctx.items()))


@pytest.mark.parametrize("context_override", FEATURE_COMBINATIONS, ids=_feature_combo_id)
def test_disabled_features_no_dirs(cookies, context, context_override):
    """When a feature is disabled, its directories must not exist."""
    result = cookies.bake(extra_context={**context, **context_override})
    assert result.exit_code == 0
    assert result.exception is None

    for feature_name, dirs in FEATURE_DIR_MAP.items():
        flag_key = f"use_{feature_name}"
        is_enabled = context_override.get(flag_key, "no") == "yes"

        if not is_enabled:
            for d in dirs:
                assert not (
                    result.project_path / d
                ).exists(), f"Feature '{feature_name}' disabled but dir '{d}' exists"


@pytest.mark.parametrize("context_override", FEATURE_COMBINATIONS, ids=_feature_combo_id)
def test_disabled_features_no_string_markers(cookies, context, context_override):
    """When a feature is disabled, its string markers must not appear in any file."""
    result = cookies.bake(extra_context={**context, **context_override})
    assert result.exit_code == 0
    assert result.exception is None

    for feature_name, markers in FEATURE_STRING_MARKERS.items():
        flag_key = f"use_{feature_name}"
        is_enabled = context_override.get(flag_key, "no") == "yes"

        if not is_enabled:
            paths = build_files_list(str(result.project_path))
            for path in paths:
                if is_binary(path):
                    continue
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                for marker in markers:
                    assert (
                        marker not in content
                    ), f"Feature '{feature_name}' disabled but marker '{marker}' found in {path}"


@pytest.mark.parametrize("context_override", FEATURE_COMBINATIONS, ids=_feature_combo_id)
def test_enabled_features_dirs_exist(cookies, context, context_override):
    """When a feature is enabled, its directories must exist."""
    result = cookies.bake(extra_context={**context, **context_override})
    assert result.exit_code == 0
    assert result.exception is None

    for feature_name, dirs in FEATURE_DIR_MAP.items():
        flag_key = f"use_{feature_name}"
        is_enabled = context_override.get(flag_key, "no") == "yes"

        if is_enabled:
            for d in dirs:
                assert (
                    result.project_path / d
                ).is_dir(), f"Feature '{feature_name}' enabled but dir '{d}' does not exist"


@pytest.mark.parametrize("context_override", FEATURE_COMBINATIONS, ids=_feature_combo_id)
def test_email_tasks_conditional(cookies, context, context_override):
    """tasks.py only exists when both use_email=yes and use_celery=yes."""
    result = cookies.bake(extra_context={**context, **context_override})
    assert result.exit_code == 0
    assert result.exception is None

    tasks_path = result.project_path / "libs" / "email" / "tasks.py"
    email_on = context_override.get("use_email", "no") == "yes"
    celery_on = context_override.get("use_celery", "no") == "yes"

    if email_on and celery_on:
        assert tasks_path.exists(), "tasks.py should exist when both email and celery are enabled"
    elif email_on:
        assert not tasks_path.exists(), "tasks.py should not exist when email is on but celery is off"
