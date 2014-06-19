# Really should do more with this...
# 

from django.http import HttpResponseRedirect

def index(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/dj/me')
	else:
		return HttpResponseRedirect('/dj/me')
