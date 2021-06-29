"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path
from opencensus.trace.span_context import generate_span_id, generate_trace_id
from rest_framework import routers
from mysite.firstapp import views
from django.conf.urls.static import static
from mysite import settings
import django.views.static as ss

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('dt', views.current_datetime),
    path('exc', views.exc),
    path('util/generate-trace-id', views.generate_trace_id),
    path('util/generate-span-id', views.generate_span_id),
    path('util/generate-traceparent', views.generate_trace_parent),
    path('util/show-request-headers', views.show_headers),
    path('util/show-date-time', views.current_datetime_indirect),
    path('graph/query', views.query_resource_graph),
    url(r'^ht/', include('health_check.urls')),
    url(r'^static/(?P<path>.*)$', ss.serve,
        {'document_root': settings.STATIC_ROOT}),
]
# + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# print(settings.STATIC_ROOT)
