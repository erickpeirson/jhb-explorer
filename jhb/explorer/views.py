from django.shortcuts import get_object_or_404, render, redirect
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect


def topics(request):
    template = loader.get_template('explorer/topics.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))

# Create your views here.
