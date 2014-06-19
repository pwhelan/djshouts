from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect

from deejaypages.forms import EditDJForm
from deejaypages.models import DJ, FacebookConnection
from deejaypages import loggedin

from filetransfers.api import prepare_upload, serve_file
from google.appengine.api import images
from google.appengine.ext import blobstore


# Edit the DJ Profile
@loggedin
def edit(request):
	try:
		dj = DJ.query(DJ.user_id==str(request.user.id)).fetch(1)[0]
	except IndexError:
		dj = DJ()
		dj.user_id = str(request.user.id)
	
	if request.method == 'POST':
		form = EditDJForm(request.POST, dj) #request.FILES)
		form.populate_obj(dj)
		dj.put()
		
		return HttpResponseRedirect('/shows/')
	
	upload_url, upload_data = prepare_upload(request, '/dj/me')
	
	if dj.picture:
		blob_info = dj.picture.file.blobstore_info
		data = blobstore.fetch_data(blob_info.key(), 0, 50000) 
		image = images.Image(image_data=data)
	else:
		image = None
	
	connections = FacebookConnection.query(
			FacebookConnection.user_id==str(request.user.id)
		).order(FacebookConnection.type).fetch()
	
	form = EditDJForm(instance=dj)
	return direct_to_template(request, 'deejaypages/dj.html', 
		{'dj': dj, 'form': form, 'logout': "/",  'facebook_id' : None,
			'nickname': request.user.first_name, 'image' : image, 'loggedin': True,
			'upload_url': upload_url, 'upload_data': upload_data,
			'connections': connections })

@loggedin
def facebook_setup(request):
	facebook_profile = request.user.get_or_create(user = u).get_facebook_profile()
	
	dj = DJ()
	dj.user_id = request.user.id
	dj.picture = download("http://graph.facebook.com/" + facebook_profile.username + "/picture?type=large")

def picture(request, id):
	dj = DJ.objects.get(id__exact=id)
	return serve_file(request, dj.picture)

def login(request):
	return direct_to_template(request, 'deejaypages/login.html', {})

