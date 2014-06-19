from google.appengine.api import users
from django.http import HttpResponseRedirect, HttpResponse
from deejaypages.models import OAuth2Token, OAuth2Service, OAuth2TokenType
from django.core.exceptions import ObjectDoesNotExist

from google.appengine.api import urlfetch
from urllib import quote as urlquote

import logging


def callback(request, servicename):
	user = users.get_current_user()
	if user is None:
		HttpResponseRedirect(users.create_login_url('/dj/me/'))
	
	service = OAuth2Service.objects.get(name=servicename)
	
	auth = OAuth2Token()
	auth.token =  request.GET['code']
	auth.type = OAuth2TokenType.AUTHORIZE
	auth.user_id = user.user_id()
	auth.service = service
	
	url = ("%s?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s" 
		% (service.access_token_url, service.client_id, 
			urlquote(service.callback_url), service.client_secret, 
			auth.token))
	
	try:
		result = urlfetch.fetch(url)
	except urlfetch.InvalidURLError, e:
		return HttpResponse('URL Error: for ' + url)
	
	logging.error('CONTENT = ' + result.content)
	(var,token) = result.content.split('=')
	
	access = OAuth2Token()
	access.token = token
	access.type = OAuth2TokenType.AUTHORIZE
	access.user_id = user.user_id()
	access.service = service
	
	access.save()
	auth.save()
	
	return HttpResponseRedirect('/dj/me')

def setup(request):
	try:
		facebook = OAuth2Service.objects.get(name='facebook')
	except ObjectDoesNotExist, e:
		facebook = OAuth2Service()
		facebook.name = 'facebook'
		facebook.client_id = '343474889029815'
		facebook.client_secret = '34522294997b9be30f39483dbc374ad6'
		facebook.access_token_url = 'https://graph.facebook.com/oauth/access_token'
		facebook.callback_url = 'http://deejaypages.appspot.com/oauth2/callback/facebook'
		facebook.save()
	
	return HttpResponse('DONE')

