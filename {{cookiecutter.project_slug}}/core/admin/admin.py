from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.waffle.admin import FlagAdmin as BaseFlagAdmin
from waffle.admin import SampleAdmin as BaseSampleAdmin
from waffle.admin import SwitchAdmin as BaseSwitchAdmin
from waffle.models import Flag
from waffle.models import Sample
from waffle.models import Switch

admin.site.unregister(Flag)
admin.site.unregister(Switch)
admin.site.unregister(Sample)


@admin.register(Flag)
class FlagAdmin(BaseFlagAdmin):
    pass


@admin.register(Switch)
class SwitchAdmin(ModelAdmin, BaseSwitchAdmin):
    pass


@admin.register(Sample)
class SampleAdmin(ModelAdmin, BaseSampleAdmin):
    pass
