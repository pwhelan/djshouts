from wtforms_appengine.ndb import model_form
from deejaypages.models import RadioStream, DJ

#class CreateShowForm(forms.ModelForm):
#	class Meta:
#		#model = RadioStream
#		exclude = ['dj', 'user_id']

#class EditDJForm(forms.ModelForm):
#	class Meta:
#		#model = DJ
#		exclude = ['user_id']

CreateShowForm = model_form(RadioStream(), only=['start', 'end'])#exclude=['dj', 'user_id'])
EditDJForm = model_form(DJ(), exclude=['user_id'])
