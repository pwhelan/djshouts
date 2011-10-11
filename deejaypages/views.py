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
	
	shows = Show.objects.filter(dj=dj).all()
		
	return direct_to_template(request, 'deejaypages/index.html',
		{'shows': shows, 'logout': users.create_logout_url("/"), 
			'form': CreateShowForm(), 'nickname' : users.get_current_user().nickname()}
	)

def view_show(request, id):
	show = Show.objects.get(id__exact=id)
	hosturl = ('https' if request.is_secure() else 'http') + '://' + request.get_host()
	flashvars = "lang=en&codec=mp3&volume=100&tracking=false&jsevents=false&autoplay=true&" + \
			"buffering=5&title=Renegade%20Radio UK&welcome=Welcome%20To the Radio"
	return direct_to_template(request, 'deejaypages/show.html', 
				{'show': show, 'flashvars' : flashvars, 'hosturl' : hosturl})

def view_show_cover(request, id, file):
	return HttpResponseRedirect('/media/placeholder.jpg')
	#return HttpResponse("FOOBAR", mimetype="text/plain")

def create_show(request):
	if request.method == 'POST':
		form = CreateShowForm(request.POST)
		if form.is_valid() or 1:	
			show = form.save(commit=False)
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
		form = EditDJForm(request.POST)
		if form.is_valid() or 1:	
			dj = form.save(commit=False)
			dj.user_id = user.user_id()
			dj.save()
		return HttpResponseRedirect('/shows/')
	
	form = EditDJForm()
	return direct_to_template(request, 'deejaypages/dj.html', 
		{'dj': dj, 'form': form, 'logout': users.create_logout_url("/"), 'nickname': user.nickname()})
