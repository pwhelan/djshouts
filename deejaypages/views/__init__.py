from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect

def index(request):
	if not request.user.is_authenticated():
		return direct_to_template(request, 'deejaypages/login.html', {})
	else:
		return HttpResponseRedirect('/dj/me')

