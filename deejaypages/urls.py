from django.conf.urls.defaults import *

urlpatterns = patterns('deejaypages.views',
	(r'^$', 'list_shows'),
	(r'(\d+)$', 'view_show'),
	(r'add$', 'create_show')
)
