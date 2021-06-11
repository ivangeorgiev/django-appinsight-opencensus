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


from contextlib import contextmanager
from opencensus.trace import execution_context
from opencensus.trace import span as span_module
from opencensus.trace import status as status_module


class OpenSpanContext:

    @property
    def tracer(self):
        return execution_context.get_opencensus_tracer()
    
    @property
    def span_context(self):
        return self.tracer.span_context

    def __init__(self, propagator=None):
        self.propagator = propagator or trace_context_http_header_format.TraceContextPropagator()

    def get_trace_headers(self):
        trace_context_headers = self.propagator.to_headers(self.span_context)
        return trace_context_headers


@contextmanager
def open_span(name=None, kind=None, attributes=None):
    context = OpenSpanContext()
    tracer = context.tracer

    if not context.tracer:
        yield context
        return

    span = tracer.start_span()
    span.name = name
    span.kind = kind or span_module.SpanKind.CLIENT

    for attr_name, attr_value in (attributes or {}).items():
        tracer.add_attribute_to_current_span(attr_name, attr_value)

    try:
        yield context
    except Exception as exc_info:
        status = status_module.Status.from_exception(exc_info)
        span.set_status(status)
        raise
    finally:
        tracer.end_span()

def _get_headers_from_request(request):
    # return {k:str(v) for k,v in request.headers}
    return {k:str(v) for k,v in request.META.items()}

def _make_json_response(data):
    return JsonResponse(data, json_dumps_params=dict(indent=2))

def show_headers(request):
    headers = _get_headers_from_request(request)
    return _make_json_response(headers)

def current_datetime_indirect(request):
    span_context = execution_context.get_opencensus_tracer().span_context
    trace_id = span_context.trace_id
    span_id = span_context.span_id

    headers = request.META
    s1 = headers.get("HTTP_X_APPSERVICE_PROTO")
    s2 = headers.get("wsgi.url_scheme")
    sheme = headers.get("HTTP_X_APPSERVICE_PROTO") or headers.get("wsgi.url_scheme") or "https"
    url = f'{sheme}://{headers["HTTP_HOST"]}/dt'
    span_attributes = dict(
        header_name = trace_context_http_header_format._TRACEPARENT_HEADER_NAME,
        url = url,
    )
    with open_span(name="GetDateTimeRemote", attributes = span_attributes) as context:
        raise Exception("Hello")
        response = requests.get(
            url,
            headers=context.get_trace_headers()
        )

    data = {
        'url': url,
        'current_datetime': datetime.datetime.now(),
        'trace_id': trace_id,
        'span_id': span_id,
        'header_name': trace_context_http_header_format._TRACEPARENT_HEADER_NAME,
    }

    template = loader.get_template('show-date-time-indirect.html')
    context = {
        'data' : data,
        'data_json': json.dumps({k:str(v) for k,v in data.items()}, indent=2),
        'response_json': json.dumps(response.json(), indent=2),
    }
    return HttpResponse(template.render(context, request))

    return _make_json_response(context)

def current_datetime(request):

    span_context = execution_context.get_opencensus_tracer().span_context
    context = {
        'current_datetime': datetime.datetime.now(),
        'trace_id': span_context.trace_id,
        'span_id': span_context.span_id,
        'traceparent_header_name': trace_context_http_header_format._TRACEPARENT_HEADER_NAME,
        'traceparent_header_value': request.headers.get(trace_context_http_header_format._TRACEPARENT_HEADER_NAME),
        'headers': _get_headers_from_request(request),
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
