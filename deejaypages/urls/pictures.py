from django.conf.urls.defaults import *

urlpatterns = patterns('deejaypages.views.pictures',
	(r'importfacebook$', 'downloadfromfacebook'),
	(r'^(.+)$', 'show')
)
