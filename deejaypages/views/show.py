from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.simple import direct_to_template
from django.utils import simplejson

from deejaypages.forms import CreateShowForm
from deejaypages.models import DJ, RadioStream
from deejaypages import loggedin

from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.ext import blobstore

from google.appengine.api import taskqueue


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

	return direct_to_template(request, 'deejaypages/index.html',
		{'logout': '/dj/logout', 'loggedin' : True, 'form': form,
			'radios': simplejson.dumps(radios), 'nickname' : request.user.email}
	)

# Show a public page for the show.
def view(request, id):
	show = ndb.Key(urlsafe=id).get()

	data = blobstore.fetch_data(show.owner.get().picture, 0, 50000)
	image = images.Image(image_data=data)

	hosturl = ('https' if request.is_secure() else 'http') \
			 + request.get_host()
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
		{'logout': "/", 'shows': shows, 'nickname' : request.user.email}
	)
