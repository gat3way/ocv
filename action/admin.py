from django.utils.safestring import mark_safe 
from django.contrib import admin
from .models import Action, Event, Alarm


class EventAdmin(admin.ModelAdmin):
    #raw_id_fields = ["user"]
    list_filter = ["name", "timestamp", "source"]
    list_display = ["timestamp", "duration_seconds", "name", "source", "user", "snapshot_url", "video_url", "comment"]
    search_fields = ["user__username", "user__email", "comment"]
    readonly_fields = ['snapshot_url','video_url']

    def snapshot_url(self,obj):
        return mark_safe(obj.get_s_url())
    def video_url(self,obj):
        return mark_safe(obj.get_v_url())

admin.site.register(Action)
admin.site.register(Event,EventAdmin)
admin.site.register(Alarm)



# Register your models here.
