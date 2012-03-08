from datetime import datetime
from pytz import timezone
import pytz

from google.appengine.api import users
from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.simple import direct_to_template
from deejaypages.forms import CreateShowForm, EditDJForm
from deejaypages.models import DJ, Show, OAuth2Access, FacebookPost, FacebookConnection
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

TOKEN_AUTHORIZE = 1
TOKEN_ACCESS = 2
TOKEN_REFRESH = 3

from webapp2_extras import jinja2

from google.appengine.api import taskqueue

# Used to list shows, it nows creates/maybe edits? them...
def list_shows(request):
	user = users.get_current_user()
	if user is None:
		return HttpResponseRedirect(users.create_login_url('/shows/'))
	
	try:
		dj = DJ.objects.get(user_id=user.user_id())
	except ObjectDoesNotExist:
		return HttpResponseRedirect('/dj/me')
	
	return direct_to_template(request, 'deejaypages/index.html',
		{'logout': users.create_logout_url("/"), 'loggedin' : True,
			'form': CreateShowForm(), 'nickname' : user.nickname()}
	)

# Show a public page for the show.
def view_show(request, id):
	show = Show.objects.get(id__exact=id)
	user = users.get_current_user()
	
	blob_info = show.dj.picture.file.blobstore_info
	data = blobstore.fetch_data(blob_info.key(), 0, 50000) 
	image = images.Image(image_data=data)
	
	hosturl = ('https' if request.is_secure() else 'http') + '://' + request.get_host()
	flashvars = "lang=en&codec=mp3&volume=100&tracking=false&jsevents=false&autoplay=true&" + \
			"buffering=5&skin=/media/ffmp3-eastanbul.xml&title=" + show.title
	return direct_to_template(request, 'deejaypages/show.html', 
				{'show': show, 'flashvars' : flashvars, 'hosturl' : hosturl,
					'logout': users.create_logout_url("/") if not user is None else '', 
					'nickname' : user.nickname() if not user is None else None,
					'user': user, 'image' : image, 
					'loggedin' : True if not user is None else False})

# Redirect to the actual player...
# Almost totally useless...
# Facebook caches the redirect almost eternally...
def view_show_player(request, id):
	show = Show.objects.get(id=id)
	hosturl = ('https' if request.is_secure() else 'http') + '://' + request.get_host()
	
	show.set_local_time('America/Vancouver')
	now = datetime.now(timezone('America/Vancouver'))
	
	if (show.local_end() > now and show.local_start() <= now or 1):
		flashplayer = hosturl + "/media/ffmp3-tiny.swf?url=" + show.url
		flashvars = "lang=en&codec=mp3&volume=100&tracking=false&jsevents=false&autoplay=true&" + \
				"buffering=5&title=" + show.title
		
	else:
		flashplayer = "http://player.soundcloud.com/player.swf?url=http%3A%2F%2Fapi.soundcloud.com%2Fusers%2F557468";
		flashvars = "show_comments=true&auto_play=false&show_playcount=true*show_artwork=true&color=ff7700"
	
	return HttpResponseRedirect(flashplayer + '&' + flashvars)

# Redirect to the actual player...
# Almost totally useless...
# Facebook caches the redirect almost eternally...
def view_show_player_skinned(request, id):
	show = Show.objects.get(id=id)
	hosturl = ('https' if request.is_secure() else 'http') + '://' + request.get_host()
	
	show.set_local_time('America/Vancouver')
	now = datetime.now(timezone('America/Vancouver'))
	
	if (show.local_end() > now and show.local_start() <= now or 1):
		flashplayer = hosturl + "/media/ffmp3-config.swf?url=" + show.url
		flashvars = "lang=en&codec=mp3&volume=100&tracking=false&jsevents=false&autoplay=true&" + \
				"skin=ffmp3-eastanbul.xml&buffering=5&title=" + show.title
		
	else:
		flashplayer = "http://player.soundcloud.com/player.swf?url=http%3A%2F%2Fapi.soundcloud.com%2Fusers%2F557468";
		flashvars = "show_comments=true&auto_play=false&show_playcount=true*show_artwork=true&color=ff7700"
	
	return HttpResponseRedirect(flashplayer + '&' + flashvars)

# Shows the cover. 'file' 
def view_show_cover(request, id, file):
	show = Show.objects.get(id__exact=id)
	return HttpResponseRedirect('/dj/picture/' + str(show.dj.id))

# Create a new Show
def create_show(request):
	
	user = users.get_current_user()
	if user is None:
		return HttpResponseRedirect(users.create_login_url('/shows/'))
	
	if request.method == 'POST':
		form = CreateShowForm(request.POST)
		if form.is_valid() or 1:	
			show = form.save(commit=False)
			
			# Change the Date to GMT
			if show.date.hour > 0:
				show.date = datetime(show.date.year, show.date.month, show.date.day, \
					show.date.hour-1, show.date.minute, tzinfo = timezone('America/Vancouver'))
			else:
				show.date = datetime(show.date.year, show.date.month, show.date.day-1, \
					23, show.date.minute, tzinfo = timezone('America/Vancouver'))
			
			show.date = show.date.astimezone(timezone('GMT'))
			
			# Add the DJ to the Show! He's mighty important
			dj = DJ.objects.get(user_id=user.user_id())
			show.dj = dj
			show.save()
			
			task = taskqueue.Task(url='/dj/facebookpost/' + str(show.id))
			task.add()
			
			return HttpResponseRedirect('/shows/' + str(show.id))
	
	return HttpResponseRedirect('/shows/')

def add_show_post(request, show_id):
	task = taskqueue.Task(url='/dj/facebookpost/' + show_id)
	task.add()
	
	return HttpResponse('Task Added')
	
# Edit the DJ Profile
def edit_dj(request):
	
	user = users.get_current_user()
	if user is None:
		return HttpResponseRedirect(users.create_login_url('/dj/me'))
	
	try:
		dj = DJ.objects.get(user_id=user.user_id())
	except ObjectDoesNotExist:
		dj = DJ()
		dj.user_id = user.user_id()
	
	try:
		oauths = OAuth2Access.objects.filter(user_id=user.user_id(), token_type = TOKEN_ACCESS).all()
		services = {}
		for oauth in oauths:
			services[oauth.service] = True
	except ObjectDoesNotExist:
		services = {}


	if request.method == 'POST':
		form = EditDJForm(request.POST, request.FILES, instance = dj)
		form.save()
				
		return HttpResponseRedirect('/shows/')
	
	upload_url, upload_data = prepare_upload(request, '/dj/me')
	
	if dj.picture:
		blob_info = dj.picture.file.blobstore_info
		data = blobstore.fetch_data(blob_info.key(), 0, 50000) 
		image = images.Image(image_data=data)
	else:
		image = None
	
	form = EditDJForm(instance=dj)
	return direct_to_template(request, 'deejaypages/dj.html', 
		{'dj': dj, 'form': form, 'logout': users.create_logout_url("/"), 
			'nickname': user.nickname(), 'image' : image, 'loggedin': True,
			'upload_url': upload_url, 'upload_data': upload_data,
			'services' : services})

def view_history(request):
	user = users.get_current_user()
	if user is None:
		return HttpResponseRedirect(users.create_login_url('/shows/'))
	
	try:
		dj = DJ.objects.get(user_id=user.user_id())
	except ObjectDoesNotExist:
		return HttpResponseRedirect('/dj/me')
	
	shows = Show.objects.filter(dj=dj).all()
	for show in shows:
		show.set_local_time('America/Vancouver')
		show.local_start = show.local_start()
		show.local_end = show.local_end()
	
	return direct_to_template(request, 'deejaypages/history.html',
		{'logout': users.create_logout_url("/"), 'shows': shows, 'nickname' : user.nickname()}
	)

	from filetransfers.api import serve_file

def oauth2_facebook(request):
	client = oauth.FacebookClient(
		consumer_key='343474889029815', 
		consumer_secret='34522294997b9be30f39483dbc374ad6', 
		callback_url='http://deejaypages.appspot.com/dj/oauth2callback/facebook'
	)
	return HttpResponseRedirect(client.get_authorization_url())

def oauth2_callback(request, service):
	user = users.get_current_user()
	if user is None:
		HttpResponseRedirect(users.create_login_url('/dj/me/'))
	
	auth = OAuth2Access()
	auth.token =  request.GET['code']
	auth.token_type = TOKEN_AUTHORIZE
	auth.user_id = user.user_id()
	auth.service = service
	auth.save()
	
	url = ("https://graph.facebook.com/oauth/access_token?client_id=343474889029815&"
		"redirect_uri=%s&"
		"client_secret=34522294997b9be30f39483dbc374ad6&code=%s" 
		% (urlquote('http://deejaypages.appspot.com/dj/oauth2callback/facebook'), auth.token))
	
	try:
		result = urlfetch.fetch(url)
	except urlfetch.InvalidURLError, e:
		return HttpResponse('URL Error: for ' + url)
	
	(var,token) = result.content.split('=')
	
	access = OAuth2Access()
	access.token = token
	access.token_type = TOKEN_ACCESS
	access.user_id = user.user_id()
	access.service = service
	access.save()
	
	return HttpResponseRedirect('/dj/me')

def get_connections(request, dj_id):
	task = taskqueue.Task(url='/dj/facebookconnections/' + dj_id)
	task.add()
	
	return HttpResponse('Task Added')

import logging

def get_facebook_connections(request, dj_id):
	try:
		dj = DJ.objects.get(id=dj_id)
	except ObjectDoesNotExist, e:
		return HttpResponse('DJ does not exist');
	
	try:
		oauth2 = OAuth2Access.objects.get(user_id=dj.user_id, token_type=TOKEN_ACCESS, service='facebook')
	except ObjectDoesNotExist, e:
		return HttpResponse('No OAuth Acess');
	
	# Load Self
	result = urlfetch.fetch(url='https://graph.facebook.com/me?access_token=' + oauth2.token,
				deadline=120,
				method=urlfetch.POST)
	
	logging.debug('JSON =' + result.content)
	me = json.loads(result.content)
	
	conn = FacebookConnection()
	conn.dj = dj
	conn.fbid = me['id']
	conn.name = me['name']
	conn.otype = CONNECTION_PROFILE
	conn.save()
	
	# Load Groups
	result = urlfetch.fetch(url='https://graph.facebook.com/me/groups?access_token=' + oauth2.token,
				deadline=120,
				method=urlfetch.POST)
	
	logging.debug('GROUPS = ' + result.content)
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

def dj_image_handler(request, id):
	dj = DJ.objects.get(id__exact=id)
	return serve_file(request, dj.picture)

def post_show_facebook(request, show):
	try:
		show = Show.objects.get(id=show)
		oauth2 = OAuth2Access.objects.get(user_id=show.dj.user_id, token_type=TOKEN_ACCESS, service='facebook')
	except ObjectDoesNotExist, e:
		return HttpResponse('Show does not exist')
	
	if (FacebookPost.objects.filter(show=show).count() > 0):
		return HttpResponse('DUPLICATE');
	
	form_fields = {
		'name': show.title,
		'message': show.description,
		'link': 'http://deejaypages.appspot.com/shows/' + str(show.id),
		'picture': 'http://deejaypages.appspot.com/dj/picture/' + str(show.dj.id),
		'source': 'http://deejaypages.appspot.com/shows/player/' + str(show.id),
		'caption': show.title
	}
	form_data = urllib.urlencode(form_fields)
	result = urlfetch.fetch(url='https://graph.facebook.com/me/feed?access_token=' + oauth2.token,
				payload=form_data,
				deadline=120,
				method=urlfetch.POST)
	
	post = FacebookPost()
	post.show = show
	post.fbid = json.loads(result.content)['id']
	post.save()
	
	return HttpResponse('SUCCESS')

