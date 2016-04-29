import json

from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.template.loader import get_template
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.template.loader import render_to_string

from podiosync.models import PodioKey, ApplicationSync
from podiosync.api import PodioApi
from podiosync.forms import PodioKeyForm

from podiosync.utils import create_model, modify_table, sync_application


# Create your views here.
def index(request):
    t = get_template('index.html')
    # get the key/user setup
    podio_setup = PodioKey.objects.all()
    sync_application(15661105, 'olivier.florentin@citrix.com')
    return HttpResponse(t.render(RequestContext(request, {'podio_setup': podio_setup})))


def orgs_list(request):
    t = get_template('orgs_list.html')
    podio_api = PodioApi('olivier.florentin@citrix.com')
    organizations = podio_api.auth.Org.get_all()
    return HttpResponse(t.render(RequestContext(request,
                                                {'organizations': organizations})))


def spaces_list(request, org_id):
    t = get_template('spaces_list.html')
    podio_api = PodioApi('olivier.florentin@citrix.com')
    organization = podio_api.auth.Org.get_one(org_id)
    workspaces_list = podio_api.auth.Space.find_available_for_org(org_id)
    workspaces_list = sorted(workspaces_list, key=lambda k: k['name'])
    return HttpResponse(t.render(RequestContext(request,
                                                {'spaces_list': workspaces_list,
                                                 'organization': organization})))


def applications_list(request, space_id):
    t = get_template('applications_list.html')
    back_id = request.GET.get('back', None)
    if back_id:
        back_url = reverse('spaces-list', args=(back_id,))
    else:
        back_url = None
    podio_api = PodioApi('olivier.florentin@citrix.com')
    podio_key_id = 2
    workspace = podio_api.auth.Space.find(space_id)
    applications_list = podio_api.auth.Application.list_in_space(space_id)
    for application in applications_list:
        if ApplicationSync.objects.filter(application_id=application['app_id']).count():
            application['sync_enabled'] = 'checked'
        else:
            application['sync_enabled'] = ''
    applications_list = sorted(applications_list, key=lambda k: k['config']['name'])
    return HttpResponse(t.render(RequestContext(request,
                                                {'applications_list': applications_list,
                                                 'podio_key_id': podio_key_id,
                                                 'space': workspace,
                                                 'back_url': back_url})))


def fields_list(request, application_id):
    t = get_template('fields_list.html')
    back_id = request.GET.get('back', None)
    if back_id:
        back_url = reverse('applications-list', args=(back_id,))
    else:
        back_url = None
    podio_api = PodioApi('olivier.florentin@citrix.com')
    application = podio_api.auth.Application.find(application_id)
    return HttpResponse(t.render(RequestContext(request,
                                                {'application': application,
                                                 'back_url': back_url})))


def application_sync(request, action_sync, application_id):
    msg = {'result': 'error'}
    application_name = request.POST.get('application_name', None)
    podio_key_id = request.POST.get('podio_key_id', None)
    try:
        app_to_update = ApplicationSync.objects.get(application_id=application_id)
        if action_sync == 'add':
            app_to_update.application_enabled = True
        elif action_sync == 'remove':
            app_to_update.application_enabled = False
        app_to_update.save()
        msg['result'] = 'success'
        msg['msg'] = 'Application updated'
    except ApplicationSync.DoesNotExist:
        if action_sync == 'add' and application_name:
            app_to_update = ApplicationSync.objects.create(application_id=application_id,
                                                           podio_key_id=podio_key_id,
                                                           application_name=application_name,
                                                           application_enabled=True)
            msg['result'] = 'success'
            msg['msg'] = 'Application updated'

    return HttpResponse(json.dumps(msg), content_type="application/json")


def edit_settings(request, form_name):
    t = get_template('edit_settings.html')
    form = PodioKeyForm()
    return HttpResponse(t.render(RequestContext(request, {'form': form})))





