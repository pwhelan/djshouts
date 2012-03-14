from datetime import datetime
from pytz import timezone
import pytz

from google.appengine.api import users
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
def create(request):
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
def view(request, id):
	show = Show.objects.get(id__exact=id)
	user = users.get_current_user()
	
	blob_info = show.dj.picture.file.blobstore_info
	data = blobstore.fetch_data(blob_info.key(), 0, 50000) 
	image = images.Image(image_data=data)
	
	hosturl = ('https' if request.is_secure() else 'http') + '://' + request.get_host()
	flashvars = "lang=en&codec=mp3&volume=100&tracking=false&jsevents=false&autoplay=true&" + \
			"buffering=5&skin=/media/ffmp3-eastanbul.xml&title=" + show.title
	flashplayer = hosturl + "/media/ffmp3-tiny.swf?url=" + show.url
	
	return direct_to_template(request, 'deejaypages/show.html', 
				{'show': show, 'flashvars' : flashvars, 'hosturl' : hosturl,
					'flashplayer' : flashplayer,
					'logout': users.create_logout_url("/") if not user is None else '', 
					'nickname' : user.nickname() if not user is None else None,
					'user': user, 'image' : image, 
					'loggedin' : True if not user is None else False})

# Redirect to the actual player...
# Almost totally useless...
# Facebook caches the redirect almost eternally...
def player(request, id):
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

# Shows the cover. 'file' 
def cover(request, id, file):
	show = Show.objects.get(id__exact=id)
	return HttpResponseRedirect('/dj/picture/' + str(show.dj.id))

# Create a new Show
def save(request):
	
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
			
			task = taskqueue.Task(url='/oauth2/facebook/task/show/' + str(show.id))
			task.add()
			
			return HttpResponseRedirect('/shows/' + str(show.id))
	
	return HttpResponseRedirect('/shows/')

def history(request):
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

