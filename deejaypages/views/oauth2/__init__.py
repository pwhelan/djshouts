from datetime import datetime
from pytz import timezone
import pytz

from google.appengine.api import users
from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.simple import direct_to_template
from deejaypages.forms import CreateShowForm, EditDJForm
from deejaypages.models import OAuth2Access, OAuth2Service, TOKEN_AUTHORIZE, TOKEN_ACCESS
from  django.core.exceptions import ObjectDoesNotExist

from filetransfers.api import prepare_upload, serve_file
from google.appengine.api import images
from google.appengine.ext import blobstore

import oauth
import urllib2
import urllib
from google.appengine.api import urlfetch
from urllib import quote as urlquote
from django.utils import simplejson as json

from webapp2_extras import jinja2
from google.appengine.api import taskqueue

import logging


def callback(request, servicename):
	user = users.get_current_user()
	if user is None:
		HttpResponseRedirect(users.create_login_url('/dj/me/'))
	
	service = OAuth2Service.objects.get(name=servicename)
	
	auth = OAuth2Access()
	auth.token =  request.GET['code']
	auth.token_type = TOKEN_AUTHORIZE
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
	
	access = OAuth2Access()
	access.token = token
	access.token_type = TOKEN_ACCESS
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

