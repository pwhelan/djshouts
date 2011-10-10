from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect
from django.views.generic.simple import direct_to_template
from deejaypages.forms import CreateShowForm
from deejaypages.models import DJ, Show

def list_shows(request):
	#dj = DJ.objects.get(user__exact==request.user)
	shows = Show.objects.all() #Shows.objects().get(dj__exact==dj)
	return direct_to_template(request, 'deejaypages/index.html',
		{'shows': shows, 'form': CreateShowForm()}
	)

def view_show(request):
	show = Show.object.get(id__exact=1)

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
