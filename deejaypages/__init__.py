from django.http import HttpResponseRedirect

def loggedin(func):
	def inner(request, *args, **kwargs):
		if not request.user.is_authenticated():
			return HttpResponseRedirect('/')
		return func(request, *args, **kwargs)
	return inner
