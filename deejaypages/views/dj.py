from datetime import datetime
from pytz import timezone
import pytz

from google.appengine.api import users
from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.simple import direct_to_template
from deejaypages.forms import EditDJForm
from deejaypages.models import DJ, OAuth2Access, TOKEN_AUTHORIZE, TOKEN_ACCESS, TOKEN_REFRESH
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

# Edit the DJ Profile
def edit(request):
	
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

def picture(request, id):
	dj = DJ.objects.get(id__exact=id)
	return serve_file(request, dj.picture)

