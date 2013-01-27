from django.conf.urls.defaults import *

urlpatterns = patterns('deejaypages.views.dj',
	(r'me$', 'edit'),
	(r'^picture/(\d+)$', 'picture'),
	(r'facebook$', 'facebook_setup')
)

