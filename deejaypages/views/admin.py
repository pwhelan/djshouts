from google.appengine.ext import ndb

from django.contrib import auth
from django.utils import simplejson
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.simple import direct_to_template

from deejaypages import adminloggedin, adminloggedinorsetup
from deejaypages.forms import UserForm


@adminloggedinorsetup
def setup(request):

	if request.method == 'POST':
		form = UserForm(request.POST) #request.FILES)
		if form.is_valid():
			user = form.save()
			user.set_password(user.password)
			user.is_superuser = True
			user.save()
			
			user.backend = 'django.contrib.auth.backends.ModelBackend'
			auth.login(request, user)

			return HttpResponseRedirect('/oauth2/')
	else:
		form = UserForm()
		return direct_to_template(request, 'admin/register.html', {'form': form})
