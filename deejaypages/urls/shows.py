from django.conf.urls.defaults import *

urlpatterns = patterns('deejaypages.views.show',
	(r'^$', 'create'),
	(r'^(\d+)$', 'view'),
	(r'^player/(\d+)$', 'player'),
	(r'^images/(\d+)/(.+)', 'cover'),
	(r'^edit/(\d+)$','edit'),
	(r'^add$', 'save'),
	(r'^save/(\d+)$', 'save'),
	(r'^history$', 'history'),
)

