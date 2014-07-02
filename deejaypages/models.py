""" Use NDB so we can take advantage of PolyModels. """
from google.appengine.ext import ndb

from google.appengine.ext.ndb import polymodel

""" Import ProtoRPC's messages so we can use Enumerators. Msgprop as well... """
from protorpc import messages
from google.appengine.ext.ndb import msgprop

from google.appengine.api.images import get_serving_url


class DJ(ndb.Model):
	""" Reference to the web authenticated user."""
	user_id		= ndb.StringProperty()

	""" The DJ's Artistic name."""
	name		= ndb.StringProperty()

	""" """
	picture		= ndb.BlobKeyProperty()

	@classmethod
	def findByUserID(cls, id):
		if not isinstance(id, basestring):
			id = str(id)

		return DJ.query(cls.user_id==str(id)).fetch(1)[0]

class OAuth2TokenType(messages.Enum):
	AUTHORIZE = 1
	ACCESS = 2
	REFRESH = 3

class OAuth2Service(ndb.Model):
	name			= ndb.StringProperty(required=True)
	access_token_url	= ndb.StringProperty(required=True)
	does_access_use_post	= ndb.BooleanProperty(default=False)
	client_id		= ndb.StringProperty(required=True)
	client_secret		= ndb.StringProperty(required=True)
	connect_url		= ndb.StringProperty(required=True)

	""" Maximum size of 250 x 30 """
	connectbutton		= ndb.BlobKeyProperty()

	def __getattr__(self, key):
		if key == 'connectbutton_url':
			return get_serving_url(self.connectbutton)

		raise AttributeError('type object \'OAuth2Service\' has no attribute \'' + key + '\'')

	def callback_url(self, request):
		return ('https' if request.is_secure() else 'http') + \
			'://' + request.get_host() + \
			'/oauth2/callback/' + self.name

class OAuth2Token(ndb.Model):
	user_id		= ndb.StringProperty(required=True)
	token		= ndb.StringProperty(required=True)
	service		= ndb.KeyProperty(kind=OAuth2Service, required=True)
	type		= msgprop.EnumProperty(OAuth2TokenType, required=True)

class OAuth2Connection(ndb.Model):
	user_id		= ndb.StringProperty(required=True)
	xid		= ndb.StringProperty(required=True)
	service		= ndb.KeyProperty(kind=OAuth2Service, required=True)

class FacebookConnectionType(messages.Enum):
	PROFILE	= 1
	PAGE	= 2
	GROUP	= 3

class FacebookConnection(ndb.Model):
	user_id		= ndb.StringProperty(required=True)
	fbid		= ndb.StringProperty(required=True)
	name		= ndb.StringProperty(required=True)
	access_token	= ndb.StringProperty()
	enabled		= ndb.BooleanProperty(default=True)
	type		= msgprop.EnumProperty(FacebookConnectionType, required=True, default=FacebookConnectionType.PROFILE)

class ExternalPicture(ndb.Model):
	url	= ndb.StringProperty()
	dim	= ndb.StringProperty()
	sx	= ndb.IntegerProperty()
	sy	= ndb.IntegerProperty()

"""
Externals are for tracking external content like Facebook posts (both originating
from the web app itself and externaly scraped), Mixcloud Sets, SoundCloud tracks,
Tweets, etc...

"""

class External(polymodel.PolyModel):
	""" Base class used to track external content."""
	owner		= ndb.KeyProperty(kind=DJ, indexed=True)
	url		= ndb.StringProperty(indexed=True)
	title		= ndb.StringProperty(indexed=True)
	description	= ndb.StringProperty(indexed=True)
	picture		= ndb.StructuredProperty(ExternalPicture)

class Track(External):
	""" Base class used for audio/video content."""
	# Might be used in a later version...
	#embed	= ndb.StringProperty()
	pass

class SoundCloudTrack(Track):
	""" Track SoundCloud tracks."""

class MixCloudTrack(Track):
	""" Track Mixcloud sets."""
	pictures	= ndb.StructuredProperty(ExternalPicture, repeated=True)

class RadioStreamType(messages.Enum):
	SHOUTCASTV1	= 1
	SHOUTCASTV2	= 2
	ICECASTV1	= 3
	ICECASTV2	= 4

class RadioStream(Track):
	protocol	= msgprop.EnumProperty(RadioStreamType, default=RadioStreamType.ICECASTV2, required=True)
	start		= ndb.DateTimeProperty(required=True, auto_now_add=True)
	end		= ndb.DateTimeProperty()
	recording	= ndb.KeyProperty(kind=Track)

class FacebookComment(ndb.Model):
	""" Track an individual comment for a Facebook post."""
	text		= ndb.StringProperty()

class FacebookPost(External):
	""" Track Facebook posts, both those created by the app and those that
	are scraped from Facebook automatically."""
	xid		= ndb.StringProperty()
	comments	= ndb.StructuredProperty(FacebookComment, repeated=True)
