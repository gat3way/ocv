from django.contrib import admin
from .models import Source, Sink, Storage

admin.site.register(Source)
admin.site.register(Sink)
admin.site.register(Storage)
