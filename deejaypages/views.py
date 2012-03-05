from datetime import datetime
from pytz import timezone
import pytz

from google.appengine.api import users
from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.simple import direct_to_template
from deejaypages.forms import CreateShowForm, EditDJForm
from deejaypages.models import DJ, Show, OAuth2Access
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
			
			return HttpResponseRedirect('/shows/' + str(show.id))
	
	return HttpResponseRedirect('/shows/')

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
			'upload_url': upload_url, 'upload_data': upload_data})

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

def dj_image_handler(request, id):
	dj = DJ.objects.get(id__exact=id)
	return serve_file(request, dj.picture)

def oauth2_facebook(request):
	client = oauth.FacebookClient(
		consumer_key='343474889029815', 
		consumer_secret='34522294997b9be30f39483dbc374ad6', 
		callback_url='http://deejaypages.appspot.com/dj/oauth2callback'
	)
	return HttpResponseRedirect(client.get_authorization_url())

TOKEN_AUTHORIZE = 1
TOKEN_ACCESS = 2
TOKEN_REFRESH = 3

def oauth2_callback(request):
	user = users.get_current_user()
	if user is None:
		HttpResponseRedirect(users.create_login_url('/dj/me/'))
	
	auth = OAuth2Access()
	auth.token =  request.GET['code']
	auth.token_type = TOKEN_AUTHORIZE
	auth.user_id = user.user_id()
	auth.save()
	
	url = ("https://graph.facebook.com/oauth/access_token?client_id=343474889029815&"
		"redirect_uri=%s&"
		"client_secret=34522294997b9be30f39483dbc374ad6&code=%s" 
		% (urlquote('http://deejaypages.appspot.com/dj/oauth2callback'), auth.token))
     	try:
		result = urllib2.urlopen(url)
	except urllib2.URLError, e:
		resulting.blah = boom
	except urllib2.HTTPError, e:
		resulting.blah = boom
	
	response = result.read()
	(var,token) = response.split('=')
	
	access = OAuth2Access()
	access.token = token
	access.token_type = TOKEN_ACCESS
	access.user_id = user.user_id()
	access.save()
	
	return HttpResponseRedirect('/dj/me')

def facebook_post(request):
	user = users.get_current_user()
	if user is None:
		HttpResponseRedirect(users.create_login_url('/dj/me/'))
	
	oauth2 = OAuth2Access.objects.get(user_id=user.user_id(), token_type=TOKEN_ACCESS)
	
	
	form_fields = {
		'token': oauth2.token,
		'message': "Phil is a Motha FUcka"
	}
	form_data = urllib.urlencode(form_fields)
	result = urlfetch.fetch(url='https://graph.facebook.com/me/feed?access_token=' + oauth2.token,
				payload=form_data,
				method=urlfetch.POST)
	
	post = json.loads(result.content)
	
	form_fields = {
		'token': oauth2.token,
		'message': "Oh YOu kNOooW he Is!"
	}
	form_data = urllib.urlencode(form_fields)
	result = urlfetch.fetch(
			url='https://graph.facebook.com/' + post['id'] + 
				'/comments?access_token=' + oauth2.token,
			payload=form_data,
			method=urlfetch.POST)
	
	return HttpResponseRedirect('/dj/me')

