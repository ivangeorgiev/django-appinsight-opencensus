from mysite import settings
import datetime
import logging
from django.shortcuts import render
from django.http import HttpResponse
import logging

# Create your views here.
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from mysite.firstapp.serializers import UserSerializer, GroupSerializer


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
