import logging
import os
import shutil

from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.conf import settings
from django.contrib.auth import get_user_model

from lineage_app.helpers import setup_oh_individual

User = get_user_model()

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def setup_user(self, user_id):
    progress_recorder = ProgressRecorder(self)
    user = User.objects.get(id=user_id)

    # create individual for this user
    individual = user.individuals.create(name='Me', openhumans_individual=True)
    try:
        setup_oh_individual(individual.pk, progress_recorder)
    except Exception as err:
        logging.error(err)
        user.setup_complete = True
        user.save()

@shared_task
def delete_user(user_id):
    user = User.objects.get(id=user_id)

    user_dir = os.path.join(settings.SENDFILE_ROOT, 'users', str(user.uuid))
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)

    user.delete()
