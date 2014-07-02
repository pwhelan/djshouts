from django.conf.urls.defaults import *

urlpatterns = patterns('deejaypages.views.admin',
	(r'$', 'setup'),
	(r'setup$', 'setup')
)
