from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.simple import direct_to_template
from deejaypages.forms import CreateShowForm
from deejaypages.models import DJ, Show

def list_shows(request):
	#dj = DJ.objects.get(user__exact==request.user)
	shows = Show.objects.all() #Shows.objects().get(dj__exact==dj)
	return direct_to_template(request, 'deejaypages/index.html',
		{'shows': shows, 'form': CreateShowForm()}
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
		print request.POST
		form = CreateShowForm(request.POST)
		if form.is_valid():	
			show = form.save(commit=False)
			if request.user.is_authenticated():
				dj = DJ.objects.get(user__exact==request.user)
				show.dj = dj
			show.save()
	return HttpResponseRedirect('/shows/')

