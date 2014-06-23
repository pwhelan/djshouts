from __future__ import with_statement
from google.appengine.api import files
from google.appengine.api import urlfetch
from google.appengine.api.images import get_serving_url

from django.http import HttpResponse, HttpResponseRedirect #, HttpResponseNotFound
from deejaypages.models import DJ
from deejaypages import loggedin


from facebook_connect.models import FacebookUser

@loggedin
def downloadfromfacebook(request):
	fb = FacebookUser.objects.get(contrib_user=request.user.id)
	
	url = "http://graph.facebook.com/" + str(fb.facebook_id) + "/picture?type=large"
	
	res = urlfetch.fetch(url)
	if res.status_code == 200:
		file_name = files.blobstore.create(mime_type='image/jpeg')
		
		# Open the file and write to it
		with files.open(file_name, 'a') as f:
			f.write(res.content)
		
		# Finalize the file. Do this before attempting to read it.
		files.finalize(file_name)
		
		# Get the file's blob key
		blob_key = files.blobstore.get_blob_key(file_name)
		
		try:
			dj = DJ.findByUserID(request.user.id)
		except IndexError:
			dj = DJ(name='<Placeholder>')
		
		dj.user_id = str(request.user.id)
		dj.picture = blob_key
		dj.put()
		
		return HttpResponse("SUCCESS")
	
	return HttpResponseRedirect('/dj/me')

def show(request, blob_key):
	url = get_serving_url(blob_key)
	return HttpResponseRedirect(url)

