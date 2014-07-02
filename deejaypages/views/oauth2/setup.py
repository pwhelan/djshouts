from __future__ import with_statement
from google.appengine.api import files
from google.appengine.ext import ndb

from django.utils import simplejson
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.simple import direct_to_template

from deejaypages import adminloggedin
from deejaypages.forms import OAuth2ServiceForm
from deejaypages.models import OAuth2Service


@adminloggedin
def create(request, key = None):
	if key:
		service = ndb.Key(urlsafe=key).get()
	else:
		service = None


	form = OAuth2ServiceForm(initial=service.to_dict() if not service == None else None)

	return direct_to_template(request, 'oauth2/service.html',
		{'loggedin' : True, 'form': form, 'is_show_page': True,
			'service': service, 'nickname' : request.user.email}
	)

# Create a new Show
@adminloggedin
def save(request, key=None):
	if request.method == 'POST':
		if key:
			service = ndb.Key(urlsafe=key).get()
		else:
			service = OAuth2Service()

		form = OAuth2ServiceForm(request.POST)
		if form.is_valid():
			service.populate(**form.cleaned_data)

			if 'connectbutton' in request.FILES.keys():
				file_name = files.blobstore.create(mime_type=request.FILES['connectbutton'].content_type)

				# Open the file and write to it
				with files.open(file_name, 'a') as f:
					f.write(request.FILES['connectbutton'].read())

				# Finalize the file. Do this before attempting to read it.
				files.finalize(file_name)

				# Get the file's blob key
				blob_key = files.blobstore.get_blob_key(file_name)
				service.connectbutton = blob_key

			service.put()
			return HttpResponse(simplejson.dumps({'key': service.key.urlsafe()}))
		else:
			raise Exception('WTF')

	return HttpResponseRedirect('/oauth2/')

@adminloggedin
def list(request):
	services = OAuth2Service.query().fetch()

	return direct_to_template(request, 'oauth2/services.html',
		{'nickname' : request.user.email, 'services': services,
		'loggedin' : True if request.user.is_authenticated() else False}
	)
