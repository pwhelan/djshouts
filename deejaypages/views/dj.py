from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect, HttpResponseNotFound

from filetransfers.api import serve_file
from google.appengine.api import images
from google.appengine.ext import blobstore

from deejaypages.forms import EditDJForm
from deejaypages.models import DJ, FacebookConnection
from deejaypages import loggedin


# Edit the DJ Profile
@loggedin
def edit(request):
	try:
		dj = DJ.findByUserID(request.user.id)
	except IndexError:
		dj = DJ()
		dj.user_id = str(request.user.id)


	if request.method == 'POST':
		form = EditDJForm(request.POST, dj) #request.FILES)
		if form.is_valid():
			dj.name = form.cleaned_data['name']
			dj.put()

		return HttpResponseRedirect('/shows/')

	#upload_url, upload_data = prepare_upload(request, '/dj/me')

	if dj.picture:
		data = blobstore.fetch_data(dj.picture, 0, 50000)
		image = images.Image(image_data=data)
	else:
		image = None

	connections = FacebookConnection.query(
			FacebookConnection.user_id==str(request.user.id)
		).order(FacebookConnection.type).fetch()


	form = EditDJForm(initial=dj.to_dict())

	return direct_to_template(request, 'deejaypages/dj.html',
		{'dj': dj, 'form': form, 'logout': "/", 'image': image,
			'nickname': request.user.email, 'is_profile_page': True,
			'loggedin': True, 'connections': connections })

@loggedin
def facebook_setup(request):
	#facebook = FacebookUser.objects.get(contrib_user=request.user.id)

	#dj = DJ()
	#dj.user_id = request.user.id
	#dj.picture = download("http://graph.facebook.com/" + facebook_profile.username + "/picture?type=large")
	return HttpResponseRedirect('/dj/me')

def picture(request, id):
	try:
		dj = DJ.findByUserID(id)
	except IndexError:
		return HttpResponseNotFound('<h1>Page not found</h1>')

	return serve_file(request, dj.picture)

def login(request):
	return direct_to_template(request, 'deejaypages/login.html', {})
