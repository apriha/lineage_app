from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid4, editable=False)
    setup_started = models.BooleanField(default=False, editable=False)
    setup_complete = models.BooleanField(default=False, editable=False)
    setup_task_id = models.UUIDField(unique=True, default=uuid4, editable=False)

    def __str__(self):
        return str(self.pk)
