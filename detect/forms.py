# forms.py
from django.db import models
from django import forms
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

from detect.models import Face


class VideoUploadWidget(forms.Widget):
    template_name = 'videoupload_widget.html'

    def render(self, name, value, attrs=None):
        context = {
            'url': '/'
        }
        return mark_safe(render_to_string(self.template_name, context))




class FacesForm(forms.ModelForm):
    name = forms.CharField()
    training_images = forms.CharField(widget=VideoUploadWidget, required=False)


    class Meta:
        model = Face
        fields = "__all__" 