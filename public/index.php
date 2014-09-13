<?php

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\RedirectResponse;

use Silex\Application;

use google\appengine\api\cloud_storage\CloudStorageTools;

use Djshouts\OAuth2;


$app->get('/', function (Silex\Application $app, Request $request) {
	
	$session = $request->getSession();
	if ($session->get('user_id'))
	{
		return new RedirectResponse('/profile');
	}
	
	$services = OAuth2\Service::all();
	return $app['view']->render('helloworld',
		['request' => $request, 'services' => $services]);
});


$profile = $app['controllers_factory'];

$profile->get('/', function(Application $app, Request $request) {
	
	$user = Djshouts\User::
			where('id', '==', $request->getSession()->get('user_id'))
			->get()
		->first();
	
	$DJ  = Djshouts\DJ::where('user', '==', $user)->first();
	if (!$DJ)
	{
		$DJ = new Djshouts\DJ;
	}
	
	
	$tokens = OAuth2\Token::where('user', '==', $user)->get();
	$services = OAuth2\Service::all();
	
	$services = $services->filter(function($service) use ($tokens) {
		
		foreach ($tokens as $token)
		{
			if ($token->service->id == $service->id)
			{
				return false;
			}
		}
		
		return true;
	});
	
	
	$app['view']->is_profile_page = true;
	
	return $app['view']->render('profile/main', [
		'tokens'	=> $tokens,
		'services'	=> $services,
		'DJ'		=> $DJ
	]);
});

$profile->post('/', function(Application $app, Request $request) {
	
	$user = Djshouts\User::
			where('id', '==', $request->getSession()->get('user_id'))
			->get()
		->first();
	
	$DJ = Djshouts\DJ::where('user', '==', $user)->first();
	if (!$DJ)
	{
		$DJ = new Djshouts\DJ;
		$DJ->user = $user;
	}
	
	foreach ($request->request->all() as $key => $value)
	{
		if ($key == 'image')
		{
			$value = Djshouts\Image::find($value);
		}
		
		$DJ->{$key} = $value;
	}
	
	$DJ->save();
	
	
	return new RedirectResponse('/profile');
});

$profile->before(function(Request $request) {
	
	if (!$request->getSession()->get('user_id'))
	{
		return new RedirectResponse('/user/login');
	}
	
});


$app->mount('/profile', $profile);



$setup = $app['controllers_factory'];


$setup->get('/', function() use ($app) {
	
	$users = Djshouts\User::all();
	if (count($users) < 1)
	{
		return new RedirectResponse('/setup/firstuser');
	}
	
	return new RedirectResponse('/setup/oauth2');
});

$setup->get('/firstuser', function() use ($app) {
	
	$users = Djshouts\User::all();
	if (count($users) >= 1)
	{
		$memcache = new Memcache;
		$memcache->set('setup_wizard_step', 1, 0, 0);
		$app->redirect('/setup/oauth2');
	}
	
	return $app['view']->render('setup/firstuser', ['is_setup' => true]);
});

$setup->post('/firstuser', function(Request $request) {
	
	$users = Djshouts\User::all();
	if (count($users) >= 1)
	{
		throw new \Exception('First user already setup');
	}
	
	$user = new Djshouts\User;
	foreach($request->request as $key => $val)
	{
		$user->{$key} = $val;
	}
	
	if ($user->save())
	{
		$memcache = new Memcache;
		$memcache->set('setup_wizard_step', 1, 0, 0);
		
		$request->getSession()->set('user_id', $user->id);
	}
	
	return new RedirectResponse('/setup');
});

$setup->post('/oauth2/{id}', function(Request $req, $id) {
	
	
	$filename = 'connect-'.
		strtolower($req->request->get('name'))
		.'-'.time().mt_rand(10, 100).'.png';
		//$req->files->get('connectbutton')->getClientOriginalExtension().'.png';
	
	$file = $req->files->get('connectbutton')->move('gs://djshouts.appspot.com/', $filename);
	
	$image = new Djshouts\Image;
	$image->filename = $file->getPathname();
	$image->save();
	
	if ($id)
	{
		$service = Djshouts\OAuth2\Service::
			where('id', '==', $id)
			->get()
			->first();
	}
	else
	{
		$service = new Djshouts\OAuth2\Service;
	}
	
	$service->connectbutton = $image;
	
	
	foreach($req->request as $key => $val)
	{
		$service->{$key} = $val;
	}
	
	$service->save();
	
	$memcache = new Memcache;
	$memcache->set('setup_wizard_step', 2, 0, 0);
	
	return json_encode($service->toArray());
	
})->value('id', 0);

$setup->get('/oauth2/{id}', function(Silex\Application $app, Request $req, $id) {
	
	if ($id)
	{
		if (is_numeric($id))
		{
			$service = Djshouts\OAuth2\Service::where('id', '==', $id)->get()->first();
		}
		else
		{
			$service = Djshouts\OAuth2\Service::where('name', '==', $id)->get()->first();
		}
	}
	else
	{
		$service = null;
	}
	
	
	$upload_url = CloudStorageTools::createUploadUrl(
		'/setup/oauth2' . (isset($service) ? '/' . $service->id : ''),
		[ 'gs_bucket_name' => 'djshouts.appspot.com' ]
	);
	
	return $app['view']->render(
		'/setup/oauth2/service',
		['is_setup' => true, 'base_url' => $upload_url, 'service' => $service]
	);
	
})->value('id', 0);


$setup->before(function(Request $request) {
	
	$memcache = new Memcache;
	$setup = $memcache->get('setup_wizard_step');
	
	if ($setup > 1)
	{
		$session = $request->getSession();
		if (!$session->get('user_id'))
		{
			throw new Exception("Permission Denied");
		}
	}
});

$app->mount('/setup', $setup);
