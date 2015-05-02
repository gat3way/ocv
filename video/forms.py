# forms.py
from django.utils.safestring import mark_safe
from django.db import models
from django import forms
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

from video.models import Source,LocalSource


class ScriptWidget(forms.Widget):
    template_name = 'source_script_widget.html'

    def render(self, name, value, attrs=None):
        context = {
            'url': '/'
        }
        return mark_safe(render_to_string(self.template_name, context))



# Below two classes are a hack to get our motion_excluded hidden input
class ModelField(forms.Field):
    #Model = Source
    #def prepare_value(self, value):
    #    if isinstance(value, self.Model):
    #        return value.id
    #    return value

    def to_python(self, value):
        #if value in self.empty_values:
        #    return None
        #try:
        #    value = self.Model.objects.get(id=value)
        #except (ValueError, self.Model.DoesNotExist):
        #    raise forms.ValidationError('%s does not exist' % self.Model.__class__.__name__.capitalize())
        return value


class CustomModelField(ModelField):
    Model = Source


class SourceForm(forms.ModelForm):
    name = forms.CharField()
    motion_exclude = forms.CharField(widget=forms.HiddenInput())
    motion_detection_exclude_zones = forms.CharField(widget=ScriptWidget, required=False)

    class Meta:
        model = Source
        fields = "__all__" 

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            motion_exclude = kwargs['instance'].motion_exclude
            kwargs.setdefault('initial', {})['motion_exclude'] = motion_exclude

        return super(SourceForm, self).__init__(*args, **kwargs)



    def save(self, force_insert=False, force_update=False, commit=True):
        m = super(SourceForm, self).save(commit=False)
        m.motion_exclude = mark_safe(self.cleaned_data['motion_exclude'])
        if commit:
            m.save()
        return m