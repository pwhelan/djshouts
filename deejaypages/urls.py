from django.conf.urls.defaults import *

urlpatterns = patterns('deejaypages.views',
	(r'^$', 'list_shows'),
	(r'^(\d+)$', 'view_show'),
	(r'^player/(\d+)$', 'view_show_player'),
	(r'^images/(\d+)/(.+)', 'view_show_cover'),
	(r'add$', 'create_show'),
	(r'me$', 'edit_dj'),
	(r'^history$', 'view_history'),
	(r'^picture/(\d+)$', 'dj_image_handler'),
	(r'^oauth2facebook$', 'oauth2_facebook'),
	(r'^oauth2callback/(.+)$', 'oauth2_callback'),
	(r'^facebookpost$', 'facebook_post')	 
)
