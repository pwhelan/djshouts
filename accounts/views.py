from django.core.cache import cache
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect
from django.views.generic.simple import direct_to_template

def create_new_user(request):
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			user = form.save(commit=False)
			# user must be active for login to work
			user.is_active = True
			user.save()
			return HttpResponseRedirect('/shows/')
	else:
		form = UserCreationForm()
		return direct_to_template(request, 
				'accounts/user_create_form.html', 
			{'form': form})

