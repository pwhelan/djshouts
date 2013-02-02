from django.conf.urls.defaults import *
from django.contrib.auth.forms import AuthenticationForm

handler500 = 'djangotoolbox.errorviews.server_error'

urlpatterns = patterns('',
	(r'^$', 'deejaypages.views.index'),
	
	#(r'^accounts/create_user/$', 'accounts.views.create_new_user'),
	#(r'^accounts/login/$', 'django.contrib.auth.views.login',
	#	{'authentication_form': AuthenticationForm,
	#	'template_name': 'accounts/login.html',}),
	#(r'^accounts/logout/$', 'django.contrib.auth.views.logout',
	#	{'next_page': '/',}),
        
        #url(r'^facebook/login$', 'facebook.views.login'),
	#url(r'^facebook/authentication_callback$', 'facebook.views.authentication_callback'),
	#url(r'^logout$', 'django.contrib.auth.views.logout'),
	(r'^facebook_connect/', include('facebook_connect.urls')),
	
	(r'^shows/', include('deejaypages.urls.shows')),
        (r'^dj/', include('deejaypages.urls.dj')),
        (r'^oauth2/', include('deejaypages.urls.oauth2'))
)

