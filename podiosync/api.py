__author__ = 'olivierf'
from pypodio2 import api, transport
from models import PodioKey


class PodioApi(object):
    def __init__(self, username):
        try:
            podio_details = PodioKey.objects.get(podio_user__user_name='%s' % username)
            self.auth = api.OAuthClient(podio_details.client_id,
                                        podio_details.client_secret,
                                        podio_details.podio_user.user_name,
                                        podio_details.podio_user.user_password,)
        except PodioKey.DoesNotExist:
            self.auth = None
        except transport.TransportException:
            self.auth = None

