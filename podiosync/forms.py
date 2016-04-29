__author__ = 'olivierf'
from django.forms import ModelForm, TextInput
from podiosync.models import PodioKey


class PodioKeyForm(ModelForm):
    class Meta:
        model = PodioKey
        fields = ['key_nickname', 'podio_user', 'application_name', 'client_id', 'client_secret']
        widgets = {
            'key_nickname': TextInput(attrs={'data-error': 'This field is required',
                                             'data-success': 'Right',
                                             'class': 'validate'}),
        }