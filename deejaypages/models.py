from datetime import datetime, timedelta

from pytz import timezone
import pytz

from django.db import models
from djangotoolbox.fields import BlobField

class DJ(models.Model):
	user_id = models.CharField(max_length=256)
	name = models.CharField(max_length=48)
	picture = models.FileField()

def defaultDateTime():
	d = datetime.now(timezone('GMT'))
	if d.minute >= 15 and d.minute < 45:
		d = datetime(d.year, d.month, d.day, d.hour, 30, tzinfo = timezone('GMT'))
	elif d.minute > 45:
		d = datetime(d.year, d.month, d.day, d.hour+1, tzinfo = timezone('GMT'))
	return d.astimezone(timezone('America/Vancouver'))

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
	title = models.CharField(max_length=64)
	description = models.TextField()
	
	def end(self):
		return self.date + timedelta(
					hours=self.duration.hour, 
					minutes=self.duration.minute
				)
	
	def start(self):
		return self.date
	
	def local_start(self):
		if not self._localtime is None:
			d = self.start()
			return datetime(d.year, d.month, d.day, d.hour, d.minute, tzinfo = timezone('GMT')).astimezone(self._localtime)
		else:
			return self.start()
	
	def local_end(self):
		if not self._localtime is None:
			d = self.end()
			return datetime(d.year, d.month, d.day, d.hour, d.minute, tzinfo = timezone('GMT')).astimezone(self._localtime)
		else:
			return self.end()
	
	def set_local_time(self, tz):
		self._localtime = timezone(tz)

class OAuth2Access(models.Model):
	user_id = models.CharField(max_length=256)
	token = models.CharField(max_length=256)
	service = models.CharField(max_length=256)
	token_type = models.IntegerField()

class FacebookPost(models.Model):
	show = models.ForeignKey(Show, null=False, blank=True)
	fbid = models.CharField(max_length=256)
