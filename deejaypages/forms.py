from django import forms
from deejaypages.models import Show, DJ

class CreateShowForm(forms.ModelForm):
	class Meta:
		model = Show
		exclude = ['dj']

class EditDJForm(forms.ModelForm):
	class Meta:
		model = DJ
		exclude = ['user_id']
