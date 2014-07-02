from django.conf.urls.defaults import *

urlpatterns = patterns('deejaypages.views.oauth2',
	(r'^callback/(.+)$', 'callback'),
	(r'^connect/(.+)$', 'connect'),
	(r'^setup/save/(.*)$', 'setup.save'),
	(r'^setup/$', 'setup.create'),
	(r'^setup/(.*)$', 'setup.create'),
	(r'^$', 'setup.list'),
	(r'^facebook$', 'facebook.connect'),
	(r'^facebook/task/show/(\d+)$', 'facebook.post_show'),
	(r'^facebook/queue/show/(\d+)$', 'facebook.queue_show'),
	(r'^facebook/task/connections/(\d+)$', 'facebook.connections'),
	(r'^facebook/queue/connections/(\d+)$', 'facebook.queue_connections')
)
