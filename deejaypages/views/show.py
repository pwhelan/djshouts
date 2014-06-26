from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.simple import direct_to_template
from django.utils import simplejson

from filetransfers.api import serve_file

from deejaypages.forms import CreateShowForm
from deejaypages.models import DJ, RadioStream, ExternalPicture
from deejaypages import loggedin

from google.appengine.ext import ndb, blobstore
from google.appengine.api import taskqueue, images
from google.appengine.api.images import get_serving_url


# Used to list shows, it nows creates/maybe edits? them...
@loggedin
def create(request):

	try:
		dj = DJ.query(DJ.user_id==str(request.user.id)).fetch(1)[0]
	except IndexError:
		return HttpResponseRedirect('/dj/me')

	try:
		show = RadioStream.query(RadioStream.owner==dj.key).order(-RadioStream.start).fetch(1)[0]
		form = CreateShowForm(initial={'url': show.url, 'title': show.title})
	except IndexError:
		form = CreateShowForm()

	radios = []
	for radio in RadioStream.query(
			RadioStream.owner==dj.key,
			distinct=['url'],
			projection=['url']
		).fetch():
		radios.append(radio.url)

	image_url = get_serving_url(dj.picture)
	data = blobstore.fetch_data(dj.picture, 0, 50000)
	image = images.Image(image_data=data)

	return direct_to_template(request, 'deejaypages/index.html',
		{'logout': '/dj/logout', 'loggedin' : True, 'form': form, 'image': image,
			'image_url': image_url, 'radios': simplejson.dumps(radios),
			'is_show_page': True, 'nickname' : request.user.email}
	)

# Show a public page for the show.
def view(request, id):
	show = ndb.Key(urlsafe=id).get()

	data = blobstore.fetch_data(show.owner.get().picture, 0, 50000)
	image = images.Image(image_data=data)

	hosturl = ('https' if request.is_secure() else 'http') \
			 + '://' + request.get_host()
	flashvars = "lang=en&codec=mp3&volume=100&tracking=false&jsevents=false&autoplay=true&" + \
			"buffering=5&title=" + show.title
	flashplayer = ('https' if request.is_secure() else 'http') + \
			'://' + request.get_host() + "/media/ffmp3-tiny.swf?url=" + show.url + '&' + flashvars

	return direct_to_template(request, 'deejaypages/show.html',
		{'show': show, 'flashvars' : flashvars, 'hosturl' : hosturl,
			'flashplayer' : flashplayer,
			'logout': '/logout' if request.user.is_authenticated() else '',
			'nickname' : request.user.first_name if request.user.is_authenticated() else None,
			'user': request.user, 'image' : image,
			'loggedin' : True if request.user.is_authenticated() else False})

def show(request, id):
	show = ndb.Key(urlsafe=id).get()
	return HttpResponseRedirect(show.url)

def picture(request, id):
	show = ndb.Key(urlsafe=id).get()
	return serve_file(request, show.picture)

def edit():
	pass

# Redirect to the actual player...
# Almost totally useless...
# Facebook caches the redirect almost eternally...
def player(request, id):
	show = ndb.Key(urlsafe=id).get()
	hosturl = ('https' if request.is_secure() else 'http') + '://' + request.get_host()

	flashplayer = hosturl + "/media/ffmp3-tiny.swf?url=" + show.url
	flashvars = "lang=en&codec=mp3&volume=100&tracking=false&jsevents=false&autoplay=true&" + \
			"buffering=5&title=" + show.title

	return HttpResponseRedirect(flashplayer + '&' + flashvars)

# Shows the cover. 'file'
def cover(request, id, file):
	show = ndb.Key(urlsafe=id).get()
	return HttpResponseRedirect('/dj/picture/' + str(show.dj.id))

# Create a new Show
@loggedin
def save(request, id=0):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/facebook/login')

	if request.method == 'POST':
		if id:
			show = ndb.Key(urlsafe=id).get()
		else:
			show = RadioStream()

		form = CreateShowForm(request.POST)
		if form.is_valid():
			# Add the DJ to the Show! He's mighty important
			dj = DJ.query(DJ.user_id==str(request.user.id)).fetch(1)[0]
			show.populate(**form.cleaned_data)
			show.user_id	= request.user.id
			show.owner	= dj.key
			show.picture	= ExternalPicture(url=get_serving_url(dj.picture))

			show.put()

			task = taskqueue.Task(url='/oauth2/facebook/task/show/' + str(show.key.urlsafe()))
			task.add()

			return HttpResponseRedirect('/shows/' + str(show.key.urlsafe()))
		else:
			print(request.POST)
			return HttpResponse("WTF?=" + str(form.is_valid()))

	return HttpResponseRedirect('/shows/')

@loggedin
def history(request):
	try:
		dj = DJ.query(DJ.user_id==str(request.user.id)).fetch(1)[0]
	except IndexError:
		return HttpResponseRedirect('/dj/me')

	shows = RadioStream.query(RadioStream.owner==dj.key).fetch()

	return direct_to_template(request, 'deejaypages/history.html',
		{'logout': "/", 'shows': shows, 'nickname' : request.user.email,
		'loggedin' : True if request.user.is_authenticated() else False,
		'is_history_page': True}
	)
