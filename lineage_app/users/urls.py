from django.urls import path
from django.conf import settings

from . import views

app_name='users'

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('complete/', views.complete, name='complete'),
    path('setup/', views.setup, name='setup'),
    path('account/', views.account, name='account'),
    path('delete/', views.delete, name='delete'),
    path(settings.DEAUTH_ROUTE, views.deauth, name='deauth'),
]

if settings.DEBUG:
    # enable creation and login of debug user during development
    urlpatterns += [
        path('login-debug/', views.login_debug, name='login_debug'),
    ]
