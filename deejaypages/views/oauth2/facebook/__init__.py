from django.http import HttpResponseRedirect, HttpResponse
from deejaypages.models import OAuth2Token, OAuth2TokenType, RadioStream, FacebookPost, FacebookConnection, FacebookConnectionType
from  django.core.exceptions import ObjectDoesNotExist


import oauth
import urllib
from google.appengine.api import urlfetch
from django.utils import simplejson as json

from google.appengine.api import taskqueue

import logging

def queue_show(request, show_id):
	task = taskqueue.Task(url='/oauth2/facebook/task/show/' + show_id)
	task.add()
	
	return HttpResponse('Task Added')

def post_show(request, show_id):
	try:
		show = RadioStream.objects.get(id=show_id)
		oauth2 = OAuth2Token.objects.get(user_id=show.user_id, type=OAuth2TokenType.ACCESS, service='facebook')
	except ObjectDoesNotExist, e:
		logging.error('Show does not exist: ' + show_id + ' for: ' + show.user_id)
		return HttpResponse('Show does not exist')
	
	for connection in FacebookConnection.objects.filter(user_id=show.user_id).filter(enabled=True).all():
		
		if (FacebookPost.objects.filter(show=show).count() > 0):
			logging.error('Duplicate posting for this show')
			continue
		
		form_fields = {
			'name': show.title,
			'message': show.description,
			'link': 'http://djshouts.php-dev.net/shows/' + str(show.id),
			'picture': 'http://djshouts.php-dev.net/dj/picture/' + str(show.dj.id),
			'type': 'video',
			'source': ('https' if request.is_secure() else 'http') + '://' + request.get_host() + 
					"/media/ffmp3-tiny.swf?url=" + urllib.quote_plus(show.url) + 
						'&title=' + urllib.quote_plus(show.title) +
						"&tracking=false&jsevents=false",
			'caption': show.title
		}
		form_data = urllib.urlencode(form_fields)
		result = urlfetch.fetch(url='https://graph.facebook.com/' + connection.fbid + '/feed?access_token=' + oauth2.token,
					payload=form_data,
					deadline=120,
					method=urlfetch.POST)
		
		res = json.loads(result.content)
		try:
			post = FacebookPost()
			post.show = show
			post.fbid = res['id']
			post.connection = connection
			post.save()
		
			logging.error('Show successfully posted')
			#return HttpResponse('SUCCESS')
		except TypeError as e:
			logging.error('Facebook Error: ' + result.content)
			#return HttpResponse('ERROR: ' + result.content)
			continue
	
	return HttpResponse('SUCCESS')

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

def connections(request, user_id):
	try:
		oauth2 = OAuth2Token.query(
			OAuth2Token.user_id==user_id, 
			OAuth2Token.type==OAuth2TokenType.ACCESS, 
			OAuth2Token.service=='facebook'
		).fetch()[0]
	except IndexError:
		return HttpResponse('No OAuth Acess');
	
	# Load Self
	result = urlfetch.fetch(url='https://graph.facebook.com/me?access_token=' + oauth2.token,
				deadline=120,
				method=urlfetch.GET)
	
	logging.warning('JSON =' + result.content)
	me = json.loads(result.content)
	
	
	try:
		conn = FacebookConnection.query(
			FacebookConnection.fbid==me['id']
		).fetch(1)[0]
	except IndexError:
		conn = FacebookConnection()
		conn.user_id = user_id
		conn.fbid = me['id']
		conn.name = me['name']
		conn.type = FacebookConnectionType.PROFILE
		conn.put()
	
	# Load Groups
	result = urlfetch.fetch(url='https://graph.facebook.com/me/groups?access_token=' + oauth2.token,
				deadline=120,
				method=urlfetch.GET)
	
	logging.warning('GROUPS = ' + result.content)
	groups = json.loads(result.content)['data']
	for group in groups:
		try:
			conn = FacebookConnection.query(
				FacebookConnection.fbid==group['id']
			).fetch(1)[0]
		except IndexError:
			conn = FacebookConnection()
			conn.user_id = user_id
			conn.fbid = group['id']
			conn.name = group['name']
			conn.type = FacebookConnectionType.GROUP
			conn.put()
	
	# Load Pages (only musician/band pages for now)
	result = urlfetch.fetch(url='https://graph.facebook.com/me/accounts?access_token=' + oauth2.token,
				deadline=120,
				method=urlfetch.GET)
	
	logging.warning('PAGES = ' + result.content)
	pages = json.loads(result.content)['data']
	for page in pages:
		logging.warning('PAGE = ' + json.dumps(page))
		#if page['category'] == 'Musician/band':
		try:
			conn = FacebookConnection.query(
				FacebookConnection.fbid==page['id']
			).fetch(1)[0]
		except IndexError:
			conn = FacebookConnection()
			conn.user_id = user_id
			conn.fbid = page['id']
			conn.name = page['name']
			conn.access_token = page['access_token']
			conn.type = FacebookConnectionType.PAGE
			conn.put()
	
	return HttpResponse('SUCCESS')
