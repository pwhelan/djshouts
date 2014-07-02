import hashlib
import datetime

from google.appengine.api import users, urlfetch
from urllib import quote as urlquote
from urlparse import urlparse, parse_qs

from django.http import HttpResponseRedirect, HttpResponse
from django.utils import simplejson
from django.contrib.auth import login
from django.contrib.auth.models import User

from deejaypages import loggedin
from deejaypages.models import OAuth2Token, OAuth2Service, OAuth2TokenType

import logging


def callback(request, servicename):
	try:
		service = OAuth2Service.query(OAuth2Service.name==servicename).fetch(1)[0]
	except IndexError:
		return HttpResponse('ERROR!')

	auth = OAuth2Token()
	auth.token =  request.GET['code']
	auth.type = OAuth2TokenType.AUTHORIZE
	auth.service = service.key


	if service.does_access_use_post:
		urlbits = urlparse(service.access_token_url)
		payload = {
			'client_id':		service.client_id,
			'client_secret':	service.client_secret,
			'redirect_uri':		service.callback_url,
			'code':			request.GET['code'],
			'grant_type':		'authorization_code'
		}
		
		result = urlfetch.fetch(
			url=urlbits.scheme + '://' + urlbits.netloc + urlbits.path,
			payload=payload,
			method=urlfetch.POST,
			headers={'Content-Type': 'application/x-www-form-urlencoded'}
		)

	else:
		url = ("%s?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s"
			% (service.access_token_url, service.client_id,
				urlquote(service.callback_url(request)), service.client_secret,
				auth.token))

		logging.error('URL = ' + url)

		try:
			result = urlfetch.fetch(url)
		except urlfetch.InvalidURLError:
			return HttpResponse('URL Error: for ' + url)

	logging.error('CONTENT = ' + result.content)
	res = parse_qs(result.content)

	access = OAuth2Token()
	access.token = res['access_token'][0]
	access.type = OAuth2TokenType.ACCESS
	access.service = service.key

	if request.user.is_authenticated():
		user = request.user

	if service.name == 'Facebook':
		result = urlfetch.fetch('https://graph.facebook.com/me?access_token=' + access.token)
		profile = simplejson.loads(result.content)

		try:
			connection = OAuth2Connection.query(
				OAuth2Connection.xid == profile['id'],
				OAuth2Connection.service == service.key
			).fetch(1)[0]

			if not request.user.is_authenticated():
				user = User.objects.get(user_id=connection.user_id)
				login(request, user)
		except:
			connection = OAuth2Connection(user_id = str(user.id),
				xid = profile['id'],
				service = service
			)

			if not request.user.is_authenticated():
				user = User(email = profile['email'],
					username = profile['email'],
					first_name = profile['first_name'],
					last_name = profile['last_name']
				)
				temp = hashlib.new('sha1')
				temp.update(str(datetime.datetime.now()))
				password = temp.hexdigest()

				user.set_password(password)
				user.save()
				connection.put()

				user.backend = 'django.contrib.auth.backends.ModelBackend'
				login(request, user)
	else:
		urlbits = urlparse.parse(service.access_token_url)
		result = urlfetch.fetch(urlbits.scheme + '://' + urlbits.netloc + '/me?access_token=' + access.token)
		profile = simplejson.loads(result.content)

		try:
			connection = OAuth2Connection.query(
				OAuth2Connection.xid == profile['id'],
				OAuth2Connection.service == service.key
			).fetch(1)[0]

			if not request.user.is_authenticated():
				user = User.objects.get(user_id=connection.user_id)
				login(request, user)
		except:
			connection = OAuth2Connection(user_id = str(user.id),
				xid = profile['id'],
				service = service
			)

			if not request.user.is_authenticated():
				user = User()
				if 'username' in profile.keys():
					user.username = profile['username']
				elif 'full_name' in profile.keys():
					user.username = profile['full_name'].replace(' ', '_')

				temp = hashlib.new('sha1')
				temp.update(str(datetime.datetime.now()))
				password = temp.hexdigest()

				user.set_password(password)
				user.save()
				connection.put()

				user.backend = 'django.contrib.auth.backends.ModelBackend'
				login(request, user)

	access.user_id = str(user.id)
	auth.user_id = str(user.id)

	access.put()
	auth.put()

	return HttpResponseRedirect('/dj/me')

def connect(request, servicename):
	try:
		service = OAuth2Service.query(OAuth2Service.name==servicename).fetch(1)[0]
	except IndexError:
		return HttpResponse('ERROR!')

	urlbits = urlparse(service.connect_url)
	params = str(urlbits.query).split('&')
	params.append('client_id=' + service.client_id)
	params.append('redirect_uri=' + service.callback_url(request))

	return HttpResponseRedirect(urlbits.scheme + '://' + urlbits.netloc + urlbits.path + '?' + '&'.join(params))
