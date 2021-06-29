from sys import exc_info
from mysite import settings
import datetime
import logging
from django.shortcuts import render
import django.http as djhttp
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.template import loader
import logging

# Create your views here.
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from mysite.firstapp.serializers import UserSerializer, GroupSerializer
import requests
from functools import lru_cache
import time
from pprint import pprint

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
import logging


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
        logging.exception(str(exc_info), exc_info=exc_info)
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

    hostname = headers["HTTP_HOST"]
    if 'localhost' in hostname:
        sheme = headers.get("HTTP_X_APPSERVICE_PROTO") or headers.get("wsgi.url_scheme") or "https"
        api_url = f'{sheme}://{headers["HTTP_HOST"]}'
    elif '-stage' in hostname:
        api_url = 'https://ddosdjango.azurewebsites.net'
    else:
        api_url = 'https://ddosdjango-stage.azurewebsites.net'
    url = f'{api_url}/dt'
    span_attributes = dict(
        header_name = trace_context_http_header_format._TRACEPARENT_HEADER_NAME,
        url = url,
    )
    with open_span(name="GetDateTimeRemote", attributes = span_attributes) as context:
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


def exc(request):
    l = logging.getLogger()
    l.info(f"You asked for an exception ({settings.session_id})")
    try:
        raise Exception(f"What are you doing here? ({settings.session_id})")
    except Exception as ei:
        l = logging.getLogger()
        l.exception(ei)
        raise


META_KEY_AUTHENTICATION = 'HTTP_AUTHENTICATION'
PARAM_TENANT = 'tenant'
PARAM_QUERY = 'q'
PARAM_TRANSFORM = 'transform'


@lru_cache
def _get_azure_token(tenant, client_id, client_secret, scope):
    with execution_context.get_opencensus_tracer().span(name='_get_azure_token'):
        auth_uri = f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token'
        response = requests.post(auth_uri,
                                data={
                                    'client_id': client_id,
                                    'client_secret': client_secret,
                                    'scope': scope,
                                    'grant_type': 'client_credentials',
                                },
                                headers={
                                    'Content-Type': 'application/x-www-form-urlencoded'
                                })
        token = response.json()
        token['expires_at'] = time.time() + token['expires_in']
        return token


def get_azure_token(tenant, client_id, client_secret, scope):
    with execution_context.get_opencensus_tracer().span(name='get_azure_token'):
        token = _get_azure_token(tenant, client_id, client_secret, scope)
        if 'expires_at' in token and token['expires_at'] <= time.time():
            _get_azure_token.cache_clear()
            token = _get_azure_token(tenant, client_id, client_secret, scope)
        return token


def query_azure_resource_graph(query: str, token):
    with execution_context.get_opencensus_tracer().span(name='query_azure_resource_graph'):
        query_uri = 'https://management.azure.com/providers/Microsoft.ResourceGraph/resources?api-version=2019-04-01'

        query_response = requests.post(query_uri,
                                    data=query.encode('utf-8'),
                                    headers={
                                        'Content-Type': 'application/json',
                                        'Authorization': f'Bearer {token}'
                                    }
                                    )
        return query_response.json()

def transform_from_rows(rows:list, columns:list):
    with execution_context.get_opencensus_tracer().span(name='transform_from_rows'):
        transformed = [{c['name']: r[i]
                        for i, c in enumerate(columns)} for r in rows]
        return transformed

def query_resource_graph(request):
    trace_id = execution_context.get_opencensus_tracer().span_context.trace_id
    logging.info(f'Trace ID: {trace_id}')

    if META_KEY_AUTHENTICATION not in request.META:
        return djhttp.HttpResponseForbidden('Missing authentication header(s).')
    parts = request.META.get(META_KEY_AUTHENTICATION).split(' ', 2)
    if len(parts) < 2:
        return djhttp.HttpResponseBadRequest("Malformed authentication header(s).")
    auth_type = parts[0]
    if auth_type.upper() != 'BASIC':
        return djhttp.HttpResponseBadRequest("Incorrect authentication type.")
    creds = parts[1].split(':', 2)
    if len(creds) < 2:
        return djhttp.HttpResponseBadRequest("Invalid credentials provided.")
    username, userpass = map(lambda x: x.strip(), creds)

    if PARAM_TENANT not in request.GET:
        return djhttp.HttpResponseBadRequest(f"Missing required parameter '{PARAM_TENANT}'")
    if PARAM_QUERY not in request.GET:
        return djhttp.HttpResponseBadRequest(f"Missing required parameter '{PARAM_QUERY}'")

    tenant = request.GET[PARAM_TENANT]
    scope = 'https://management.azure.com/.default'
    token = get_azure_token(tenant, username, userpass, scope)
    logging.info('Authenticated')

    query = request.GET[PARAM_QUERY]
    query_json = query_azure_resource_graph(query, token['access_token'])
    logging.info('Query response received')
    query_json['trace_id'] = trace_id

    transform = request.GET.get(PARAM_TRANSFORM, 'none').lower()
    if transform == 'none':
        pass
    elif transform == 'from_rows':
        query_json['rows'] = transform_from_rows(query_json['data']['rows'], query_json['data']['columns'])
    else:
        return djhttp.HttpResponseBadRequest(f"Invalid value for parameter '{PARAM_TRANSFORM}'")
    return(djhttp.JsonResponse(query_json))
