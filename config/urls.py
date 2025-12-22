# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('events:play')),  # OR 'game:play'
    path('accounts/', include('apps.accounts.urls')),
    path('wallet/', include('apps.wallet.urls')),
    path('game/', include('apps.events.urls')),  # OR include('apps.game.urls')
]