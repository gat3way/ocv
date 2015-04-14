from django.shortcuts import render

# Create your views here.

# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from .models import Face
from .forms import FacesForm

def list(request):
    # Handle file upload
    if request.method == 'POST':
        form = FacesForm(request.POST, request.FILES)
        if form.is_valid():
            #newdoc = Document(docfile = request.FILES['docfile'])
            #newdoc.save()

            # Redirect to the document list after POST
            return HttpResponseRedirect(reverse('detect.views.list'))
    else:
        form = DacesForm() # A empty, unbound form

    # Load documents for the list page
    #documents = Document.objects.all()

    # Render list page with the documents and the form
    return render_to_response(
        'list.html',
        {'form': form},
        context_instance=RequestContext(request)
    )