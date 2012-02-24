from datetime import datetime
from pytz import timezone
import pytz

from google.appengine.api import users
from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.simple import direct_to_template
from deejaypages.forms import CreateShowForm, EditDJForm
from deejaypages.models import DJ, Show
from  django.core.exceptions import ObjectDoesNotExist


def list_shows(request):
	user = users.get_current_user()
	if user is None:
		return HttpResponseRedirect(users.create_login_url('/shows/'))
	
	try:
		dj = DJ.objects.get(user_id=user.user_id())
	except ObjectDoesNotExist:
		return HttpResponseRedirect('/dj/me')
	
	return direct_to_template(request, 'deejaypages/index.html',
		{'logout': users.create_logout_url("/"), 
			'form': CreateShowForm(), 'nickname' : user.nickname()}
	)

def view_show(request, id):
	show = Show.objects.get(id__exact=id)
	hosturl = ('https' if request.is_secure() else 'http') + '://' + request.get_host()
	flashvars = "lang=en&codec=mp3&volume=100&tracking=false&jsevents=false&autoplay=true&" + \
			"buffering=5&title=Renegade%20Radio UK&welcome=Welcome%20To the Radio"
	return direct_to_template(request, 'deejaypages/show.html', 
				{'show': show, 'flashvars' : flashvars, 'hosturl' : hosturl, 'user': None})

def view_show_player(request, id):
	show = Show.objects.get(id=id)
	hosturl = ('https' if request.is_secure() else 'http') + '://' + request.get_host()
	
	show.set_local_time('America/Vancouver')
	now = datetime.now(timezone('America/Vancouver'))
	
	if (show.local_end() > now and show.local_start() <= now):
		flashplayer = hosturl + "/media/ffmp3-tiny.swf?url=" + show.url
		flashvars = "lang=en&codec=mp3&volume=100&tracking=false&jsevents=false&autoplay=true&" + \
				"buffering=5&title=Renegade%20Radio UK&welcome=Welcome%20To the Radio"
		
	else:
		flashplayer = "http://player.soundcloud.com/player.swf?url=http%3A%2F%2Fapi.soundcloud.com%2Fusers%2F557468";
		flashvars = "show_comments=true&auto_play=false&show_playcount=true*show_artwork=true&color=ff7700"
	
	return HttpResponseRedirect(flashplayer + '&' + flashvars)

def view_show_cover(request, id, file):
	return HttpResponseRedirect('/media/placeholder.jpg')
	#return HttpResponse("FOOBAR", mimetype="text/plain")

def create_show(request):
	if request.method == 'POST':
		form = CreateShowForm(request.POST)
		if form.is_valid() or 1:	
			show = form.save(commit=False)
			
			# Change the Date to GMT
			show.date = datetime(show.date.year, show.date.month, show.date.day, show.date.hour-1, show.date.minute, tzinfo = timezone('America/Vancouver'))
			show.date = show.date.astimezone(timezone('GMT'))
			
			# Add the DJ to the Show! He's mighty important
			user = users.get_current_user()
			if not user is None:
				dj = DJ.objects.get(user_id=user.user_id())
				show.dj = dj
			show.save()
	return HttpResponseRedirect('/shows/')

def edit_dj(request):
	
	user = users.get_current_user()
	try:
		dj = DJ.objects.get(user_id=user.user_id())
	except ObjectDoesNotExist:
		dj = DJ()
		dj.user_id = user.user_id()
	
	if request.method == 'POST':
		form = EditDJForm(request.POST, instance = dj)
		form.save()
		return HttpResponseRedirect('/shows/')
	
	form = EditDJForm(instance=dj)
	return direct_to_template(request, 'deejaypages/dj.html', 
		{'dj': dj, 'form': form, 'logout': users.create_logout_url("/"), 'nickname': user.nickname()})

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
