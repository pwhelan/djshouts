<?php

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\RedirectResponse;

use Silex\Application;

use google\appengine\api\cloud_storage\CloudStorageTools;

use Djshouts\OAuth2;


$user = $app['controllers_factory'];

$user->get('/login', function (Request $request) {
	
	$session = $request->getSession();
	if ($session->get('user_id'))
	{
		return new RedirectResponse('/profile');
	}
	
	$username = $request->server->get('PHP_AUTH_USER');
	$password = $request->server->get('PHP_AUTH_PW');
	
	
	$user = Djshouts\User::where(function($q) use ($username, $password) {
		$q->where('email', '==', $username);
		$q->where('password', '==', $password);
	})->first();
	
	if (!$user)
	{
		$user = Djshouts\User::where(function($q) use ($username, $password) {
			$q->where('username', '==', $username);
			$q->where('password', '==', $password);
		})->first();
	}
	
	if ($user)
	{
		$session->set('user_id', $user->id);
		return new RedirectResponse('/profile');
	}
	
	return new Response('Please sign in.', 401, [
		'WWW-Authenticate' => sprintf('Basic realm="%s"', 'site_login'),
	]);
});

$user->get('/logout', function (Request $request) {
	
	$session = $request->getSession();
	$session->clear();
	$session->save();
	
	return new RedirectResponse("/");
});

$user->get('/account', function (Request $request) {
	$session = $request->getSession();
	
	if (null === $user = $session->get('user')) {
		return new RedirectResponse('/login');
	}
	
	return sprintf('Welcome %s!', $user['username']);
});

$app->mount('/user', $user);
