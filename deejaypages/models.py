import datetime
from pytz import timezone
import pytz

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
	
	tz = timezone('America/Vancouver')
	d = datetime.datetime.now(tz)
	if d.minute < 15:
		d = datetime.datetime(d.year, d.month, d.day, d.hour, 0)
	elif d.minute >= 15 and d.minute < 45:
		d = datetime.datetime(d.year, d.month, d.day, d.hour, 30)
	else:
		d = datetime.datetime(d.year, d.month, d.day, d.hour+1, 0)
	
	date = models.DateTimeField(default=d)
	duration = models.TimeField()
	
	def end(self):
		return self.date + datetime.timedelta(
					hours=self.duration.hour, 
					minutes=self.duration.minute
				)
