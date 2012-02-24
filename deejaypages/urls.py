from django.conf.urls.defaults import *

urlpatterns = patterns('deejaypages.views',
	(r'^$', 'list_shows'),
	(r'^(\d+)$', 'view_show'),
	(r'^player/(\d+)$', 'view_show_player'),
	(r'^images/(\d+)/(.+)', 'view_show_cover'),
	(r'add$', 'create_show'),
	(r'me$', 'edit_dj'),
	(r'^history$', 'view_history')
)
