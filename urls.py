from django.conf.urls.defaults import *
from django.contrib.auth.forms import AuthenticationForm

handler500 = 'djangotoolbox.errorviews.server_error'

urlpatterns = patterns('',
	(r'^$', 'django.views.generic.simple.redirect_to', {'url': '/shows/', }),
	(r'^accounts/create_user/$', 'accounts.views.create_new_user'),
	(r'^accounts/login/$', 'django.contrib.auth.views.login',
		{'authentication_form': AuthenticationForm,
		'template_name': 'accounts/login.html',}),
	(r'^accounts/logout/$', 'django.contrib.auth.views.logout',
		{'next_page': '/',}),
        (r'^shows/', include('deejaypages.urls')),
        (r'^dj/', include('deejaypages.urls')),
)
