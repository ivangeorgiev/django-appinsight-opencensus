from mysite import settings
import datetime
import logging
from django.shortcuts import render
import django.http as djhttp
from django.http import HttpResponse, HttpResponseBadRequest
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


def current_datetime(request):
    now = datetime.datetime.now()
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


META_KEY_AUTHENTICATION = 'HTTP_AUTHENTICATION'
PARAM_TENANT = 'tenant'
PARAM_QUERY = 'q'
PARAM_TRANSFORM = 'transform'


@lru_cache
def _get_azure_token(tenant, client_id, client_secret, scope):
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
    token = _get_azure_token(tenant, client_id, client_secret, scope)
    if 'expires_at' in token and token['expires_at'] <= time.time():
        _get_azure_token.cache_clear()
        token = _get_azure_token(tenant, client_id, client_secret, scope)
    return token


def query_azure_resource_graph(query: str, token):
    query_uri = 'https://management.azure.com/providers/Microsoft.ResourceGraph/resources?api-version=2019-04-01'

    query_response = requests.post(query_uri,
                                   data=query.encode('utf-8'),
                                   # json=query,
                                   headers={
                                       'Content-Type': 'application/json',
                                       'Authorization': f'Bearer {token}'
                                   }
                                   )
    return query_response.json()


def query_resource_graph(request):
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

    query = request.GET[PARAM_QUERY]
    query_json = query_azure_resource_graph(query, token['access_token'])

    transform = request.GET.get(PARAM_TRANSFORM, 'none').lower()
    if transform == 'none':
        pass
    elif transform == 'from_rows':
        columns = query_json['data']['columns']
        rows = query_json['data']['rows']
        transformed = [{c['name']: r[i]
                        for i, c in enumerate(columns)} for r in rows]
        # transformed = [r for r in rows]
        print(transformed)
        query_json['data']['rows'] = transformed
        query_json['rows'] = transformed
    else:
        return djhttp.HttpResponseBadRequest(f"Invalid value for parameter '{PARAM_TRANSFORM}'")
    return(djhttp.JsonResponse(query_json))
    print(query_json)

    pprint(token)
    print('You got me')
    query = request.GET.get('q')
    authentication = request.META.get('HTTP_AUTHENTICATION')

    print(query)
    print(authentication)
    print(request.META.keys())
    return HttpResponse('Hi')
