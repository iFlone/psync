from __future__ import unicode_literals
from django.utils.translation import ugettext as _
from django.db import models

# Create your models here.
class PodioKey(models.Model):
    key_nickname = models.CharField(max_length=150)
    podio_user = models.ForeignKey('PodioUser')
    application_name = models.CharField(max_length=150, help_text=_("Application Name (as specified in Podio)"))
    client_id = models.CharField(max_length=150, help_text=_("Client ID (as specified in Podio)"))
    client_secret = models.CharField(max_length=150, help_text=_("Client Secret (as specified in Podio)"))

    def __unicode__(self):
        return self.key_nickname


class PodioUser(models.Model):
    user_name = models.CharField(max_length=150, help_text=_("Username for the Podio User"))
    user_password = models.CharField(max_length=150, help_text=_("Password for the Podio User"))

    def __unicode__(self):
        return self.user_name


class ApplicationSync(models.Model):
    application_id = models.IntegerField()
    application_name = models.CharField(max_length=255)
    application_enabled = models.BooleanField(default=False)
    last_synced = models.DateTimeField(blank=True, null=True)
    podio_key = models.ForeignKey(PodioKey)
