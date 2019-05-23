import logging
import json

from django.shortcuts import render, redirect
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from .tasks import setup_user, delete_user
from lineage_app.openhumans.helpers import get_auth_url, login_member
from lineage_app.openhumans.models import OpenHumansMember

User = get_user_model()

logger = logging.getLogger(__name__)


def login_user(request):
    context = {"auth_url": get_auth_url()}
    return render(request, "users/login.html", context=context)


@login_required
def logout_user(request):
    logout(request)
    return redirect("index")


def login_debug(request):
    try:
        user = User.objects.get(username="debug_user")
    except ObjectDoesNotExist:
        user = User.objects.create_user("debug_user")
        user.setup_complete = True
        user.save()

    if user is not None:
        login(request, user)

    return redirect("index")


def complete(request):
    """ Receive user from Open Humans. Store data. Login user. """

    logger.debug("Received user returning from Open Humans.")

    login_member(request)

    if not request.user.is_authenticated:
        logger.debug("Invalid code exchange.")
        return redirect("index")

    if request.user.setup_complete:
        return redirect("index")
    else:
        return redirect("users:setup")


@login_required
def setup(request):
    if request.user.setup_complete:
        return redirect("index")

    if not request.user.setup_started:
        request.user.setup_started = True
        request.user.save()
        setup_user.apply_async(
            (request.user.id,), task_id=str(request.user.setup_task_id)
        )

    return render(
        request,
        "users/setup.html",
        context={"task_id": str(request.user.setup_task_id)},
    )


@login_required
def account(request):
    return render(request, "users/account.html")


@csrf_exempt
def deauth(request):
    """ Delete user and user data on OH disconnect. """

    # extract OH member ID from OH POST request
    body_unicode = request.body.decode("utf-8")
    body = json.loads(json.loads(body_unicode))
    project_member_id = int(body["project_member_id"])

    # get OH user
    oh_member = OpenHumansMember.objects.filter(oh_id=project_member_id)
    if len(oh_member) == 1:
        delete_user.delay(oh_member[0].user.id)

    return redirect("index")


@login_required
def delete(request):
    """ Delete user and user data on form submit. """

    if request.method == "POST":
        user_id = request.user.id
        logout(request)
        delete_user.delay(user_id)

    return redirect("index")
