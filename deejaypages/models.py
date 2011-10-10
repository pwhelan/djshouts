import datetime
from django.db import models
from django.contrib.auth.models import User
from djangotoolbox.fields import BlobField

class DJ(models.Model):
	user = models.ForeignKey(User, null=True, blank=True)
	name = models.CharField(max_length=48)
	image = BlobField()

class Show(models.Model):
	dj = models.ForeignKey(DJ, null=True, blank=True)
	url = models.CharField(max_length=256)
	description = models.TextField()
	date = models.DateTimeField()
	duration = models.TimeField()
	
	def end(self):
		return self.date + datetime.timedelta(
					hours=self.duration.hour, 
					minutes=self.duration.minute
				)
