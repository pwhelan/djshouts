from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
        url(r'^channel\.html$', 'facebook_connect.views.channel_url', name='channel_url'),
        url(r'^$', 'facebook_connect.views.facebook_connect', name='facebook_connect'),
    )

