import logging

from django.conf import settings
import ohapi
from django.contrib.auth import login
from .models import OpenHumansMember

logger = logging.getLogger(__name__)

def get_auth_url():
    if settings.OPENHUMANS_CLIENT_ID:
        auth_url = ohapi.api.oauth2_auth_url(
            client_id=settings.OPENHUMANS_CLIENT_ID,
            redirect_uri=settings.OPENHUMANS_REDIRECT_URI)
    else:
        auth_url = None
    return auth_url


def get_create_member(data):
    """
    use the data returned by `ohapi.api.oauth2_token_exchange`
    and return an oh_member object
    """
    oh_id = ohapi.api.exchange_oauth2_member(
        access_token=data['access_token'])['project_member_id']

    try:
        oh_member = OpenHumansMember.objects.get(oh_id=oh_id)
        logger.debug('Member {} re-authorized.'.format(oh_id))
        oh_member.access_token = data['access_token']
        oh_member.refresh_token = data['refresh_token']
        oh_member.token_expires = OpenHumansMember.get_expiration(data['expires_in'])
    except OpenHumansMember.DoesNotExist:
        oh_member = OpenHumansMember.create(oh_id=oh_id, data=data)
        logger.debug('Member {} created.'.format(oh_id))

    oh_member.save()

    return oh_member


def oh_code_to_member(code):
    """
    Exchange code for token, use this to create and return OpenHumansMember.
    If a matching OpenHumansMember already exists in db, update and return it.
    """
    if not (settings.OPENHUMANS_CLIENT_ID and
            settings.OPENHUMANS_CLIENT_SECRET and code):
        logger.error('OPENHUMANS_CLIENT info or code are unavailable')
        return None
    try:
        data = ohapi.api.oauth2_token_exchange(
            client_id=settings.OPENHUMANS_CLIENT_ID,
            client_secret=settings.OPENHUMANS_CLIENT_SECRET,
            code=code,
            redirect_uri=settings.OPENHUMANS_REDIRECT_URI)
    except Exception as err:
        logger.debug(err)
        return None

    if 'error' in data:
        logger.debug('Error in token exchange: {}'.format(data))
        return None

    if 'access_token' in data:
        return get_create_member(data)
    else:
        logger.warning('Neither token nor error info in OH response!')
        return None


def login_member(request):
    code = request.GET.get('code', '')
    oh_member = oh_code_to_member(code=code)
    if oh_member:
        # Log in the user.
        user = oh_member.user
        login(request, user)
