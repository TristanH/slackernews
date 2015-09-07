from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^$', 'main.views.home', name='home'),
    url(r'^savesettings/?$', 'main.views.save_settings', name='save_settings'),
    url(r'^getstories/(?P<offset>[0-4]{1})/?$', 'main.views.get_stories', name='get_stories'),
    url(r'^oauth/?$', 'main.views.oauth', name='oauth'),
    url(r'^settings/(?P<webhook_url_end>[/\w]+)/?$', 'main.views.change_settings', name='change_settings'),
    url(r'^admin/', include(admin.site.urls)),
]
