""" Use NDB so we can take advantage of PolyModels. """
from google.appengine.ext import ndb

from google.appengine.ext.ndb import polymodel

""" Import ProtoRPC's messages so we can use Enumerators. Msgprop as well... """
from protorpc import messages
from google.appengine.ext.ndb import msgprop


class DJ(ndb.Model):
	""" Reference to the web authenticated user."""
	user_id		= ndb.StringProperty()
	
	""" The DJ's Artistic name."""
	name		= ndb.StringProperty()
	
	""" """
	picture		= ndb.BlobKeyProperty()

class OAuth2TokenType(messages.Enum):
	AUTHORIZE = 1
	ACCESS = 2
	REFRESH = 3

class OAuth2Service(ndb.Model):
	name			= ndb.StringProperty(required=True)
	access_token_url	= ndb.StringProperty(required=True)
	client_id		= ndb.StringProperty(required=True)
	client_secret		= ndb.StringProperty(required=True)
	callback_url		= ndb.StringProperty(required=True)

class OAuth2Token(ndb.Model):
	owner		= ndb.KeyProperty(kind=DJ, required=True)
	token		= ndb.StringProperty(required=True)
	service		= ndb.KeyProperty(kind=OAuth2Service, required=True)
	type		= ndb.EnumProperty(OAuth2TokenType, required=True)

class FacebookConnectionType(messages.Enum):
	PROFILE = 1
	GROUP = 2
	PAGE = 3

class FacebookConnection(ndb.Model):
	owner		= ndb.KeyProperty(kind=DJ, required=True)
	fbid		= ndb.StringProperty(required=True)
	name		= ndb.StringProperty(required=True)
	access_token	= ndb.StringProperty()
	enabled		= ndb.BooleanProperty(default=True)
	type		= ndb.EnumProperty(FacebookConnectionType, required=True, default=FacebookConnectionType.PROFILE)

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
	owners		= ndb.KeyProperty(kind=DJ, repeated=True, indexed=True)
	title		= ndb.StringProperty()
	description	= ndb.StringProperty()
	picture		= ndb.StructuredProperty(ExternalPicture)

class Track(External):
	""" Base class used for audio/video content."""
	url		= ndb.StringProperty()
	
	# Might be used in a later version...
	#embed	= ndb.StringProperty()

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
