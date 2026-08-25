from django.urls import reverse_lazy


def sidebar_navigation(request):
    return [
        {
            "title": "Navigation",
            "separator": False,
            "items": [
                {
                    "title": "Dashboard",
                    "icon": "dashboard",
                    "link": reverse_lazy("admin:index"),
                },
            ],
        },
        {
            "title": "Authentication",
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": "Users",
                    "icon": "people",
                    "link": reverse_lazy("admin:authentication_user_changelist"),
                },
                {
                    "title": "Groups",
                    "icon": "groups",
                    "link": reverse_lazy("admin:auth_group_changelist"),
                },
            ],
        },
        {%- if cookiecutter.use_celery == "yes" %}
        {
            "title": "Celery Tasks",
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": "Periodic Tasks",
                    "icon": "schedule",
                    "link": reverse_lazy("admin:django_celery_beat_periodictask_changelist"),
                },
                {
                    "title": "Crontabs",
                    "icon": "event_repeat",
                    "link": reverse_lazy("admin:django_celery_beat_crontabschedule_changelist"),
                },
                {
                    "title": "Intervals",
                    "icon": "timer",
                    "link": reverse_lazy("admin:django_celery_beat_intervalschedule_changelist"),
                },
                {
                    "title": "Solar Events",
                    "icon": "wb_sunny",
                    "link": reverse_lazy("admin:django_celery_beat_solarschedule_changelist"),
                },
                {
                    "title": "Clocked",
                    "icon": "alarm",
                    "link": reverse_lazy("admin:django_celery_beat_clockedschedule_changelist"),
                },
                {%- if cookiecutter.use_redis == "no" %}
                {
                    "title": "Task Results",
                    "icon": "fact_check",
                    "link": reverse_lazy("admin:django_celery_results_taskresult_changelist"),
                },
                {
                    "title": "Group Results",
                    "icon": "account_tree",
                    "link": reverse_lazy("admin:django_celery_results_groupresult_changelist"),
                },
                {%- endif %}
            ],
        },
        {%- endif %}
        {
            "title": "Control Room",
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": "Dashboard",
                    "icon": "space_dashboard",
                    "link": reverse_lazy("dj_control_room:index"),
                },
                {%- if cookiecutter.use_redis == "yes" %}
                {
                    "title": "Redis",
                    "icon": "database",
                    "link": reverse_lazy("dj_redis_panel:index"),
                },
                {
                    "title": "Cache",
                    "icon": "cached",
                    "link": reverse_lazy("dj_cache_panel:index"),
                },
                {%- endif %}
                {%- if cookiecutter.use_celery == "yes" %}
                {
                    "title": "Celery",
                    "icon": "task_alt",
                    "link": reverse_lazy("dj_celery_panel:index"),
                },
                {%- endif %}
                {
                    "title": "URLs",
                    "icon": "link",
                    "link": "/admin/dj-urls-panel/?namespace=api:v1",
                },
                {
                    "title": "Signals",
                    "icon": "sensors",
                    "link": reverse_lazy("dj_signals_panel:index"),
                },
            ],
        },
        {
            "title": "Feature Flags",
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": "Flags",
                    "icon": "flag",
                    "link": reverse_lazy("admin:waffle_flag_changelist"),
                },
                {
                    "title": "Switches",
                    "icon": "toggle_on",
                    "link": reverse_lazy("admin:waffle_switch_changelist"),
                },
                {
                    "title": "Samples",
                    "icon": "science",
                    "link": reverse_lazy("admin:waffle_sample_changelist"),
                },
            ],
        },
        {
            "title": "System",
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": "Site Configuration",
                    "icon": "settings",
                    "link": reverse_lazy("admin:constance_config_changelist"),
                },
                {%- if cookiecutter.use_auditlog == "yes" %}
                {
                    "title": "Audit Logs",
                    "icon": "history",
                    "link": reverse_lazy("admin:auditlog_logentry_changelist"),
                },
                {%- endif %}
            ],
        },
    ]
