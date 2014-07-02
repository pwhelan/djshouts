from django import forms
from django.contrib.auth.models import User


class EditDJForm(forms.Form):
	name		= forms.CharField()

class ExternalForm(forms.Form):
	url		= forms.URLField()
	title		= forms.CharField()
	description	= forms.CharField(widget=forms.Textarea())

class TrackForm(ExternalForm):
	pass

class CreateRadioStreamForm(TrackForm):
	#protocol	= forms.ChoiceField(
	#	choices = (
	#		(1, 'ShoutCast V1'),
	#		(2, 'ShoutCast V2'),
	#		(3, 'Icecast V1'),
	#		(4, 'Icecast V2')
	#	),
	#	initial=4
	#)
	#start		= forms.DateTimeField()
	#end		= forms.DateTimeField()
	pass

class CreateShowForm(CreateRadioStreamForm):
	pass

class OAuth2ServiceForm(forms.Form):
	name			= forms.CharField(required=True)
	access_token_url	= forms.URLField(required=True)
	connect_url		= forms.URLField(required=True)
	client_id		= forms.CharField(required=True)
	client_secret		= forms.CharField(required=True)
	#is_post			= forms.
	""" Maximum size of 250 x 30 """
	#connectbutton		= ndb.BlobKeyProperty()

class UserForm(forms.ModelForm):
	password = forms.CharField(widget=forms.PasswordInput())

	class Meta:
		model = User
		fields = ('username', 'email', 'password')
