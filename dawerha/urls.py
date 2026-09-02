"""
URL configuration for dawerha project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

admin.site.site_header = 'لوحة التحكم'
admin.site.site_title = 'دوّرها'
admin.site.index_title = 'نظرة عامة على المنصة'

urlpatterns = [
    path('admin/', RedirectView.as_view(url='/super-admin-8790-panel/', permanent=False)),
    path('admin', RedirectView.as_view(url='/super-admin-8790-panel/', permanent=False)),
    # مسار لوحة الإدارة معرّف بشكل غير سهل التخمين
    path('super-admin-8790-panel/', admin.site.urls),
    path('', include('companies.urls')),
    path('game/', include('game.urls')),
    path('influencers/', include('influencers.urls')),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


