import datetime
from pytz import timezone
import pytz

from django.db import models
from djangotoolbox.fields import BlobField

class DJ(models.Model):
	user_id = models.CharField(max_length=256)
	name = models.CharField(max_length=48)

def defaultDateTime():
	tz = timezone('America/Vancouver')
	d = datetime.datetime.now(tz)
	if d.minute < 15:
		d = datetime.datetime(d.year, d.month, d.day, d.hour, 0)
	elif d.minute >= 15 and d.minute < 45:
		d = datetime.datetime(d.year, d.month, d.day, d.hour, 30)
	else:
		d = datetime.datetime(d.year, d.month, d.day, d.hour+1, 0)
	return d

class Show(models.Model):
	DURATION_CHOICES = (
		('00:30', 'Half an Hour'),
		('01:00', 'An Hour'),
		('01:30', 'An Hour and a Half'),
		('02:00', 'Two Hours'),
		('03:00', 'Three Hours')
	)
	
	dj = models.ForeignKey(DJ, null=True, blank=True)
	url = models.CharField(max_length=256)
	date = models.DateTimeField(default=defaultDateTime())
	duration = models.TimeField()
	description = models.TextField()
	
	def end(self):
		return self.date + datetime.timedelta(
					hours=self.duration.hour, 
					minutes=self.duration.minute
				)

