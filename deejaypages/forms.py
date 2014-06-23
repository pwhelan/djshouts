from django import forms


class EditDJForm(forms.Form):
	name		= forms.CharField()

class ExternalForm(forms.Form):
	title		= forms.CharField()
	description	= forms.CharField(widget=forms.Textarea())
	url		= forms.URLField()

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
