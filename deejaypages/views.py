from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.simple import direct_to_template
from deejaypages.forms import EditDJForm
from deejaypages.models import DJ, OAuth2Access, TOKEN_AUTHORIZE, TOKEN_ACCESS, TOKEN_REFRESH
from  django.core.exceptions import ObjectDoesNotExist

def index(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/dj/me') # return direct_to_template(request, 'deejaypages/logind.html', {})
	else:
		return HttpResponseRedirect('/dj/me')

