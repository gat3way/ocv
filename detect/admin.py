from django.contrib import admin
from .models import FaceRecognizer, SmokeRecognizer, Face
from .forms import FacesForm

class FaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'recognizer', 'active')
    list_filter = ('name', 'recognizer', 'active')
    form = FacesForm


admin.site.register(Face, FaceAdmin)
admin.site.register(FaceRecognizer)
admin.site.register(SmokeRecognizer)

# Register your models here.
