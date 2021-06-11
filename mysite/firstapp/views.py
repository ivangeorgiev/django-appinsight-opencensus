from sys import exc_info
from mysite import settings
import datetime
import logging
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
import logging

# Create your views here.
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from mysite.firstapp.serializers import UserSerializer, GroupSerializer

import opencensus.trace.span_context as sc
from opencensus.trace import execution_context
from opencensus.trace.propagation import trace_context_http_header_format
import requests
import json

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


def home(request):
    template = loader.get_template('index.html')
    context = {}
    return HttpResponse(template.render(context, request))

def generate_span_id(request):
    span_id = sc.generate_span_id()
    return HttpResponse(span_id)

def generate_trace_id(request):
    trace_id = sc.generate_trace_id()
    return HttpResponse(trace_id)

def generate_trace_parent(request):
    version = '00'
    trace_id = sc.generate_trace_id()
    span_id = sc.generate_span_id()
    trace_options = '01'
    traceparent = f'{version}-{trace_id}-{span_id}-{trace_options}'
    return HttpResponse(traceparent)



def _make_json_response(data):
    return JsonResponse(data, json_dumps_params=dict(indent=2))

def show_headers(request):
    headers = {k:str(v) for k,v in request.META.items()}
    print(headers)
    return _make_json_response(headers)

def current_datetime_indirect(request):
    headers = request.META
    url = f'{headers["wsgi.url_scheme"]}://{headers["HTTP_HOST"]}/dt'
    span_context = execution_context.get_opencensus_tracer().span_context
    propagator = trace_context_http_header_format.TraceContextPropagator()
    trace_context_header = propagator.to_headers(span_context)
    response = requests.get(
        url,
        headers=trace_context_header
    )

    data = {
        'url': url,
        'current_datetime': datetime.datetime.now(),
        'trace_id': span_context.trace_id,
        'span_id': span_context.span_id,
        'response': response.json(),
    }

    template = loader.get_template('show-date-time-indirect.html')
    context = {
        'data' : data,
        'data_json': json.dumps({k:str(v) for k,v in data.items()}, indent=2),
    }
    return HttpResponse(template.render(context, request))

    return _make_json_response(context)

def current_datetime(request):

    span_context = execution_context.get_opencensus_tracer().span_context
    context = {
        'current_datetime': datetime.datetime.now(),
        'trace_id': span_context.trace_id,
        'span_id': span_context.span_id,
    }
    return _make_json_response(context)
    return JsonResponse(context, json_dumps_params=dict(indent=2))

    html = "<html><body>It is now %s (%s).</body></html>" % (now,
                                                             settings.session_id)
    l = logging.getLogger('baobab')
    l.info(f'{settings.session_id}: current_date: {html}')
    return HttpResponse(html)


def exc(request):
    l = logging.getLogger()
    l.info(f"You asked for an exception ({settings.session_id})")
    try:
        raise Exception(f"What are you doing here? ({settings.session_id})")
    except Exception as ei:
        l = logging.getLogger()
        l.exception(ei)
        raise
