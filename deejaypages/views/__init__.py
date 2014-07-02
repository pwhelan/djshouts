from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.contrib.auth.models import User

def index(request):
	if not request.user.is_authenticated():
		if User.objects.count() <= 0:
			return HttpResponseRedirect('/admin/setup')
		else:
			return direct_to_template(request, 'deejaypages/login.html', {})
	else:
		return HttpResponseRedirect('/dj/me')
