"""
URL configuration for dawerha project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # مسار لوحة الإدارة معرّف بشكل غير سهل التخمين
    path('super-admin-8790-panel/', admin.site.urls),
    path('', include('companies.urls')),
    path('game/', include('game.urls')),
    path('influencers/', include('influencers.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


