from datetime import datetime
from pytz import timezone
import pytz

from google.appengine.api import users
from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.simple import direct_to_template
from deejaypages.forms import CreateShowForm, EditDJForm
from deejaypages.models import OAuth2Access, OAuth2Service, Show, DJ, FacebookPost, FacebookConnection, TOKEN_ACCESS
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

import oauth
import logging

def queue_show(request, show_id):
	task = taskqueue.Task(url='/oauth2/facebook/task/show/' + show_id)
	task.add()
	
	return HttpResponse('Task Added')

def post_show(request, show_id):
	try:
		show = Show.objects.get(id=show_id)
		oauth2 = OAuth2Access.objects.get(user_id=show.dj.user_id, token_type=TOKEN_ACCESS, service='facebook')
	except ObjectDoesNotExist, e:
		logging.error('Show does not exist: ' + show_id + ' for: ' + show.dj.user_id)
		return HttpResponse('Show does not exist')
	
	if (FacebookPost.objects.filter(show=show).count() > 0):
		logging.error('Duplicate posting for this show')
		return HttpResponse('DUPLICATE');
	
	form_fields = {
		'name': show.title,
		'message': show.description,
		'link': 'http://deejaypages.appspot.com/shows/' + str(show.id),
		'picture': 'http://deejaypages.appspot.com/dj/picture/' + str(show.dj.id),
		'type': 'video',
		'source': ('https' if request.is_secure() else 'http') + '://' + request.get_host() + "/media/ffmp3-tiny.swf?url=" + show.url,
		'caption': show.title
	}
	form_data = urllib.urlencode(form_fields)
	result = urlfetch.fetch(url='https://graph.facebook.com/me/feed?access_token=' + oauth2.token,
				payload=form_data,
				deadline=120,
				method=urlfetch.POST)
	
	res = json.loads(result.content)
	try:
		post = FacebookPost()
		post.show = show
		post.fbid = res['id']
		post.save()
		
		logging.error('Show successfully posted')
		return HttpResponse('SUCCESS')
	except TypeError, e:
		logging.error('Facebook Error: ' + result.content)
		return HttpResponse('ERROR: ' + result.content)

def connect(request):
	client = oauth.FacebookClient(
		consumer_key='343474889029815', 
		consumer_secret='34522294997b9be30f39483dbc374ad6', 
		callback_url='http://deejaypages.appspot.com/oauth2/callback/facebook'
	)
	return HttpResponseRedirect(client.get_authorization_url())

def queue_connections(request, dj_id):
	task = taskqueue.Task(url='/oauth2/facebook/task/connections/' + dj_id)
	task.add()
	
	return HttpResponse('Task Added')

def connections(request, dj_id):
	try:
		dj = DJ.objects.get(id=dj_id)
	except ObjectDoesNotExist, e:
		return HttpResponse('DJ does not exist');
	
	try:
		oauth2 = OAuth2Access.objects.get(user_id=dj.user_id, token_type=TOKEN_ACCESS, service='facebook')
	except ObjectDoesNotExist, e:
		return HttpResponse('No OAuth Acess');
	
	# Load Self
	#result = urlfetch.fetch(url='https://graph.facebook.com/me?access_token=' + oauth2.token,
	#			deadline=120,
	#			method=urlfetch.POST)
	
	#logging.warning('JSON =' + result.content)
	#me = json.loads(result.content)
	
	#conn = FacebookConnection()
	#conn.dj = dj
	#conn.fbid = me['id']
	#conn.name = me['name']
	#conn.otype = CONNECTION_PROFILE
	#conn.save()
	
	# Load Groups
	result = urlfetch.fetch(url='https://graph.facebook.com/me/groups?access_token=' + oauth2.token,
				deadline=120,
				method=urlfetch.POST)
	
	logging.warning('GROUPS = ' + result.content)
	groups = json.loads(result.content)['data']
	for group in groups:
		conn = FacebookConnection()
		conn.dj = dj
		conn.fbid = group['id']
		conn.name = group['name']
		conn.otype = CONNECTION_GROUP
		conn.save()
	
	# Load Pages (only musician/band pages for now)
	result = urlfetch.fetch(url='https://graph.facebook.com/me/accounts?access_token=' + oauth2.token,
				deadline=120,
				method=urlfetch.POST)
	
	logging.warning('PAGES = ' + result.content)
	pages = json.loads(result.content)['data']
	for page in pages:
		if page['cagetory'] == 'Musician/Band':
			conn = FacebookConnection()
			conn.dj = dj
			conn.fbid = page['id']
			conn.name = page['name']
			conn.otype = CONNECTION_PAGE
			conn.save()
	
	return HttpResponse('SUCCESS')

