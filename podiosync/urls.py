__author__ = 'olivierf'
from django.conf.urls import url
from . import views as podiosync_views

urlpatterns = [
    url(r'^$', podiosync_views.index, name='index'),
    url(r'^list/org/$', podiosync_views.orgs_list, name='orgs-list'),
    url(r'^list/space/(?P<org_id>[^/]+)/$', podiosync_views.spaces_list, name='spaces-list'),
    url(r'^list/applications/(?P<space_id>[^/]+)/$', podiosync_views.applications_list, name='applications-list'),
    url(r'^list/fields/(?P<application_id>[^/]+)/$', podiosync_views.fields_list, name='fields-list'),
    url(r'^sync/application/(?P<action_sync>[^/]+)/(?P<application_id>[^/]+)/$', podiosync_views.application_sync, name='application-sync'),
    url(r'^edit/settings/(?P<form_name>[^/]+)/$', podiosync_views.edit_settings, name='edit-settings'),
]