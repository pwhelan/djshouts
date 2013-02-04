from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.simple import direct_to_template
from deejaypages.forms import EditDJForm
from deejaypages.models import DJ, OAuth2Access, TOKEN_AUTHORIZE, TOKEN_ACCESS, TOKEN_REFRESH, FacebookConnection
from django.core.exceptions import ObjectDoesNotExist

from filetransfers.api import prepare_upload, serve_file
from google.appengine.api import images
from google.appengine.ext import blobstore

import oauth
import urllib2
import urllib
from google.appengine.api import urlfetch
from django.utils import simplejson as json

from django.contrib.auth.models import AnonymousUser

from facebook_connect.models import FacebookUser

# Edit the DJ Profile
def edit(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	
	f_user = FacebookUser.objects.get(contrib_user=request.user.id)
	facebook_profile = None
	
	try:
		dj = DJ.objects.get(user_id=request.user.id)
	except ObjectDoesNotExist:
		dj = DJ()
		dj.user_id = request.user.id
	
	try:
		oauths = OAuth2Access.objects.filter(user_id=request.user.id, token_type = TOKEN_ACCESS).all()
		services = {}
		for oauth in oauths:
			services[oauth.service] = True
			fb_profile = urllib.urlopen('https://graph.facebook.com/me?access_token=%s' % oauth.token)
			facebook_profile = json.load(fb_profile)
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
	
	try:
		connections = FacebookConnection.objects.filter(user_id=request.user.id).all()
	except ObjectDoesNotExist, e:
		connections = None
		# Queue Connections Task
	
	
	form = EditDJForm(instance=dj)
	return direct_to_template(request, 'deejaypages/dj.html', 
		{'dj': dj, 'form': form, 'logout': "/",  'facebook_id' : f_user.facebook_id,
			'nickname': request.user.username, 'image' : image, 'loggedin': True,
			'upload_url': upload_url, 'upload_data': upload_data,
			'services' : services, 'connections': connections })

def facebook_setup(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	
	facebook_profile = request.user.get_or_create(user = u).get_facebook_profile()
	
	dj = DJ()
	dj.user_id = request.user.id
	dj.picture = download("http://graph.facebook.com/" + facebook_profile.username + "/picture?type=large")

def picture(request, id):
	dj = DJ.objects.get(id__exact=id)
	return serve_file(request, dj.picture)

def login(request):
	return direct_to_template(request, 'deejaypages/login.html', {})

