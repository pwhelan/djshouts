from django.db import models
from djangotoolbox.fields import BlobField

class DJ(models.Model):
	user_id = models.CharField(max_length=256)
	name = models.CharField(max_length=48)
	picture = models.FileField()

class Show(models.Model):
	dj = models.ForeignKey(DJ, null=True, blank=True)
	url = models.CharField(max_length=256)
	title = models.CharField(max_length=64)
	description = models.TextField()
	
TOKEN_AUTHORIZE = 1
TOKEN_ACCESS = 2
TOKEN_REFRESH = 3

class OAuth2Access(models.Model):
	user_id = models.CharField(max_length=256)
	token = models.CharField(max_length=256)
	service = models.CharField(max_length=256)
	token_type = models.IntegerField()

class OAuth2Service(models.Model):
	name = models.CharField(max_length=256)
	access_token_url = models.CharField(max_length=256)
	client_id = models.CharField(max_length=256)
	client_secret = models.CharField(max_length=256)
	callback_url = models.CharField(max_length=256)

CONNECTION_PROFILE = 1
CONNECTION_GROUP = 2
CONNECTION_PAGE = 3

class FacebookConnection(models.Model):
	dj = models.ForeignKey(DJ, null=False, blank=False)
	fbid = models.CharField(max_length=256)
	name = models.CharField(max_length=256)
	access_token = models.CharField(max_length=256)
	enabled = models.BooleanField(default=False)
	otype = models.IntegerField()

class FacebookPost(models.Model):
	show = models.ForeignKey(Show, null=False, blank=False)
	to = models.CharField(max_length=256)
	fbid = models.CharField(max_length=256)
	connection = models.ForeignKey(FacebookConnection, null=False, blank=False)

