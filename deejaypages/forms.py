from django import forms
from deejaypages.models import Show

class CreateShowForm(forms.ModelForm):
	class Meta:
		model = Show
		exclude = ['dj']
