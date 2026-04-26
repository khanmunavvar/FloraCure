from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static

# Customize admin site header
admin.site.site_header  = "FloraCure Admin"
admin.site.site_title   = "FloraCure Admin Portal"
admin.site.index_title  = "Welcome to FloraCure Admin"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('floraApp.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
