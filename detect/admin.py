from django.contrib import admin
from .models import Recognizer, Face
from .forms import FacesForm

class FaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'recognizer', 'active')
    list_filter = ('name', 'recognizer', 'active')
    form = FacesForm


admin.site.register(Face, FaceAdmin)
admin.site.register(Recognizer)

# Register your models here.
