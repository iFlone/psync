from django.contrib import admin
from podiosync.models import PodioKey, PodioUser, ApplicationSync
# Register your models here.

class ApplicationSyncAdmin(admin.ModelAdmin):
    list_display = ('application_id', 'application_name', 'application_enabled', 'last_synced')

admin.site.register(PodioKey)
admin.site.register(PodioUser)
admin.site.register(ApplicationSync, ApplicationSyncAdmin)
