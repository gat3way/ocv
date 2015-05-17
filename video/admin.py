from django.contrib import admin
from .models import Source, Sink, Storage, LocalSource
from video.forms import SourceForm
from django.utils.translation import ugettext, ugettext_lazy as _


class SourceAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name', 'url', 'active', 'device', 'store_archive', 'storage')}),
        (_('Sinks'), {'fields': ('raw_sink', 'overlay_sink')}),
        (_('Black Margins'), {'fields': ('top_blank_pixels', 'left_blank_pixels','bottom_blank_pixels', 'right_blank_pixels')}),
        (_('Motion Detection'), {'fields': ('motion_detection', 'tamper_detection', 'motion_threshold', 'motion_exclude', 'motion_detection_exclude_zones')}),
        (_('IVS'), {'fields': ('face_recognizer', 'smoke_detector')}),
        )

    list_display = ('name', 'url', 'active', 'motion_detection')
    form = SourceForm


class LocalSourceAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name', 'height', 'width','color', 'fps')}),
        (_('Authentication'), {'fields': ('username', 'password','requireadmincredentials')}),
        (_('Streams'), {'fields': ('videourl', 'audiourl')}),
        (_('PTZ'), {'fields': ('ptz_type', 'ptz_control', 'ptz_step_min', 'ptz_step_max','ptz_min','ptz_max','ptz_up','ptz_up_data', 'ptz_up_right','ptz_up_right_data', 'ptz_right','ptz_right_data', 'ptz_bottom_right','ptz_bottom_right_data', 'ptz_bottom','ptz_bottom_data', 'ptz_bottom_left','ptz_bottom_left_data', 'ptz_left','ptz_left_data', 'ptz_up_left','ptz_up_left_data')}),
        (_('Modes'), {'fields': ('reseturl', 'resetdata', 'resetcontrol', 'nightmodeurl', 'nightmodedata', 'nightmodecontrol', 'daymodeurl', 'daymodedata', 'daymodecontrol','automodeurl', 'automodedata', 'automodecontrol', 'profileurl', 'profiledata', 'profilecontrol')}),
    )



admin.site.register(Source,SourceAdmin)
admin.site.register(LocalSource, LocalSourceAdmin)
admin.site.register(Sink)
admin.site.register(Storage)
