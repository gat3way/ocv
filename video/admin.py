from django.contrib import admin
from .models import Source, Sink, Storage
from video.forms import SourceForm

class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'active', 'motion_detection')
    form = SourceForm


admin.site.register(Source,SourceAdmin)
admin.site.register(Sink)
admin.site.register(Storage)
