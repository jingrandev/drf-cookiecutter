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
            ],
        },
        {%- endif %}
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
