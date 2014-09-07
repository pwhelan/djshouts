<?php

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\RedirectResponse;

use Silex\Application;

use google\appengine\api\cloud_storage\CloudStorageTools;

use Deejaypages\OAuth2;

$app->get('/', function (Silex\Application $app, Request $request) {
	
	$session = $request->getSession();
	if ($session->get('user_id'))
	{
		return new RedirectResponse('/profile');
	}
	
	$services = \Deejaypages\OAuth2\Service::all();
	return $app['view']->render('helloworld',
		['request' => $request, 'services' => $services]);
});


$setup = $app['controllers_factory'];

$setup->get('/', function() use ($app) {
	$users = Deejaypages\User::all();
	if (count($users) < 1)
	{
		return new RedirectResponse('/setup/firstuser');
	}
	
	return new RedirectResponse('/setup/oauth2');
});

$setup->get('/firstuser', function() use ($app) {
	
	$users = Deejaypages\User::all();
	if (count($users) >= 1)
	{
		$memcache = new Memcache;
		$memcache->set('setup_wizard_step', 1, 0, 0);
		$app->redirect('/setup/oauth2');
	}
	
	$app['mthaml']->render('setup/firstuser', ['is_setup' => true]);
});

$setup->post('/firstuser', function() use ($app) {
	$users = Deejaypages\User::all();
	if (count($users) >= 1)
	{
		$app->error();
		die("NO NO NO!");
	}
	
	$user = new Deejaypages\User;
	foreach($app->request->post() as $key => $val)
	{
		$user->{$key} = $val;
	}
	
	if ($user->save())
	{
		$memcache = new Memcache;
		$memcache->set('setup_wizard_step', 1, 0, 0);
	}
	
	$app->redirect('/setup');
});

$setup->get('/oauth2', function() use ($app) {
	
	$services = Deejaypages\OAuth2\Service::all();
	if (count($services) >= 1)
	{
		$memcache = new Memcache;
		$memcache->set('setup_wizard_step', 2, 0, 0);
		$app->redirect('/');
	}
	
	return $app['view']->render('/setup/oauth2/service', ['is_setup' => true]);
});

$setup->post('/oauth2/(:id)', function($id = 0) use ($app) {
	
	$service = new Deejaypages\OAuth2\Service;
	foreach($app->request->post() as $key => $val)
	{
		$service->{$key} = $val;
	}
	
	if ($service->save())
	{
		$memcache = new Memcache;
		$memcache->set('setup_wizard_step', 2, 0, 0);
	}
	
	return new RedirectResponse('/setup');
});

$app->mount('/setup', $setup);
