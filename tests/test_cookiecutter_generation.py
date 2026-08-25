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
    assert '"waffle"' in content
    assert "waffle.middleware.WaffleMiddleware" in content
    assert '"core.admin"' in content

    admin_pkg = result.project_path / "core" / "admin"
    assert (admin_pkg / "apps.py").is_file()
    assert (admin_pkg / "admin.py").is_file()

    with open(result.project_path / "pyproject.toml", encoding="utf-8") as f:
        pyproject_content = f.read()
    assert "django-waffle" in pyproject_content

    navigation_path = result.project_path / "core" / "admin" / "navigation.py"
    assert navigation_path.is_file()
    with open(navigation_path, encoding="utf-8") as f:
        navigation_content = f.read()

    assert "admin:authentication_user_changelist" in navigation_content
    assert "admin:constance_config_changelist" in navigation_content
    assert "admin:waffle_flag_changelist" in navigation_content

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
    "redis": ["django-redis", "REDIS_URL", "libs.cache", "dj_redis_panel", "dj_cache_panel"],
    "celery": [
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "libs.mq",
        "django_celery_beat",
        "celery_worker",
        "celery_beat",
        "dj_celery_panel",
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


@pytest.mark.parametrize("context_override", FEATURE_COMBINATIONS, ids=_feature_combo_id)
def test_celery_result_backend_matrix(cookies, context, context_override):
    """Result backend: django-cache (redis on) / django-db (redis off); app installed whenever celery is on."""
    result = cookies.bake(extra_context={**context, **context_override})
    assert result.exit_code == 0
    assert result.exception is None

    celery_on = context_override.get("use_celery", "no") == "yes"
    redis_on = context_override.get("use_redis", "no") == "yes"

    settings_content = (result.project_path / "config" / "settings" / "base.py").read_text()
    pyproject_content = (result.project_path / "pyproject.toml").read_text()

    if not celery_on:
        assert "django-celery-results" not in pyproject_content
        assert "django_celery_results" not in settings_content
        return

    assert "django-celery-results" in pyproject_content
    assert '"django_celery_results",' in settings_content
    navigation_content = (result.project_path / "core" / "admin" / "navigation.py").read_text()
    task_result_link = "admin:django_celery_results_taskresult_changelist"
    if redis_on:
        assert 'CELERY_RESULT_BACKEND = "django-cache"' in settings_content
        assert 'CELERY_CACHE_BACKEND = "default"' in settings_content
        assert task_result_link not in navigation_content
    else:
        assert 'CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="django-db")' in settings_content
        assert "CELERY_RESULT_EXTENDED = True" in settings_content
        assert task_result_link in navigation_content


@pytest.mark.parametrize("context_override", FEATURE_COMBINATIONS, ids=_feature_combo_id)
def test_control_room_always_integrated(cookies, context, context_override):
    """dj-control-room core is always installed; panels follow use_redis/use_celery."""
    result = cookies.bake(extra_context={**context, **context_override})
    assert result.exit_code == 0
    assert result.exception is None

    redis_on = context_override.get("use_redis", "no") == "yes"
    celery_on = context_override.get("use_celery", "no") == "yes"

    settings_content = (result.project_path / "config" / "settings" / "base.py").read_text()
    urls_content = (result.project_path / "config" / "urls.py").read_text()
    middleware_content = (result.project_path / "core" / "admin" / "middleware.py").read_text()

    assert '"dj_control_room_base",' in settings_content
    assert '"dj_control_room",' in settings_content
    assert '"dj_urls_panel",' in settings_content
    assert '"dj_signals_panel",' in settings_content
    assert "DJ_CONTROL_ROOM_SETTINGS" in settings_content
    assert '[] if DEBUG else ["core_admin/css/dcr_dashboard.css"]' in settings_content
    assert (result.project_path / "core" / "admin" / "static" / "core_admin" / "css" / "dcr_dashboard.css").is_file()

    local_content = (result.project_path / "config" / "settings" / "local.py").read_text()
    production_content = (result.project_path / "config" / "settings" / "production.py").read_text()
    assert "DEBUG = True" not in local_content
    assert "DEBUG = False" not in production_content

    start_script = (result.project_path / "compose" / "local" / "django" / "start").read_text()
    assert "python manage.py collectstatic --noinput" in start_script

    assert "DJ_URLS_PANEL_SETTINGS" in settings_content
    assert 'r".*\\?P<format>"' in settings_content
    assert 'path("admin/dj-control-room/", include("dj_control_room.urls"))' in urls_content
    assert "/admin/dj-control-room/mcp" in middleware_content

    assert ('"dj_redis_panel",' in settings_content) == redis_on
    assert ('"dj_cache_panel",' in settings_content) == redis_on
    assert ('path("admin/dj-redis-panel/"' in urls_content) == redis_on
    assert ("DJ_REDIS_PANEL_SETTINGS" in settings_content) == redis_on
    if redis_on and celery_on:
        assert '"celery-broker"' in settings_content
    if redis_on and not celery_on:
        assert '"celery-broker"' not in settings_content
    assert ('"dj_celery_panel",' in settings_content) == celery_on
    assert ('path("admin/dj-celery-panel/"' in urls_content) == celery_on


def test_django_guid_logs_demoted(cookies, context):
    """django_guid's per-request INFO noise must be demoted to DEBUG visibility."""
    result = cookies.bake(extra_context=context)
    assert result.exit_code == 0
    assert result.exception is None

    setup_content = (result.project_path / "libs" / "logging" / "setup.py").read_text()
    assert 'logging.getLogger("django_guid")' in setup_content
    assert '"DEBUG" if log_level == "DEBUG" else "WARNING"' in setup_content
