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
	
	return $app['view']->render('setup/firstuser', ['is_setup' => true]);
});

$setup->post('/firstuser', function(Request $request) {
	
	$users = Deejaypages\User::all();
	if (count($users) >= 1)
	{
		throw new \Exception('First user already setup');
	}
	
	$user = new Deejaypages\User;
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

	$file = $req->files->get('connectbutton')->move('gs://djshouts/', $filename);
	
	$image = new Deejaypages\Image;
	$image->filename = $file->getPathname();
	$image->save();
	
	if ($id)
	{
		$service = Deejaypages\OAuth2\Service::
			where('id', '==', $id)
			->get()
			->first();
	}
	else
	{
	$service = new Deejaypages\OAuth2\Service;
	}
	$service->connectbutton = $image->url;
	
	foreach($req->request as $key => $val)
	{
		$service->{$key} = $val;
	}
	
	if ($service->save())
	{
		$memcache = new Memcache;
		$memcache->set('setup_wizard_step', 2, 0, 0);
	}
	
	return json_encode($service->toArray());
	
})->value('id', 0);

$setup->get('/oauth2/{id}', function(Silex\Application $app, $id) {
	
	
	if ($id)
	{
		if (is_numeric($id))
		{
			$service = Deejaypages\OAuth2\Service::where('id', '==', $id)->get()->first();
		}
		else
		{
			$service = Deejaypages\OAuth2\Service::where('name', '==', $id)->get()->first();
		}
	}
	else
	{
		$service = null;
	}
	
	$options = [ 'gs_bucket_name' => 'djshouts' ];
	$upload_url = CloudStorageTools::createUploadUrl(
		'/setup/oauth2' . (isset($service) ? '/' . $service->id : ''),
		$options
	);
	
	return $app['view']->render(
		'/setup/oauth2/service',
		['is_setup' => true, 'base_url' => $upload_url, 'service' => $service]
	);
	
})->value('id', 0);


$setup->before(function(Request $request) {
	
	$memcache = new Memcache;
	$setup = $memcache->get('setup_wizard_step');
	
	if ($setup >= 1)
	{
		$session = $request->getSession();
		if (!$session->get('user_d'))
		{
			
		}
	}
});

$app->mount('/setup', $setup);
$oauth2 = $app['controllers_factory'];

$oauth2->get('/callback/{servicename}', function(Request $request, $servicename) {
	
	$session = $request->getSession();
	
	$user = Deejaypages\User::where('id', '==', $session->get('user_id'))->get()->first();
	if (!$user)
	{
		$user = new Deejaypages\User;
		$user->username = 'user_'.mt_rand(100, 10000);
		$user->password = mt_rand(1000000000, 100000000000);
		
		$user->save();
		$session->set('user_id', $user->id);
	}
	
	$service = OAuth2\Service::where('name', '==', $servicename)->get()->first();
	
	$token = new OAuth2\Token;
	$token->user	= $user->key;
	$token->service	= $service->key;
	$token->type	= OAuth2\Token::TYPE_AUTHORIZE;
	
	$parameters = [
		'client_id'	=> $service->client_id,
		'client_secret'	=> $service->client_secret,
		'redirect_uri'	=> $request->getScheme() ."://" .
			$request->getHttpHost() . '/oauth2/callback/' .
			$service->name,
		'code'		=> $request->get('code')
	];
	
	$url = parse_url($service->access_token_url);
	if (isset($url['query']) && strlen($url['query']) > 0)
	{
		$extra = []; parse_str($url['query'], $extra);
		$parameters = array_merge($parameters, $extra);
		
		$access_token_url = $url['scheme'] . '://' . $url['host'] . $url['path'];
	}
	else
	{
		$access_token_url = $service->access_token_url;
	}
	
	
	try {
		if ($service->is_post)
		{
			$response = GuzzleHttp\post($access_token_url,[
				'headers'	=> [
					'Accept' => 'application/json',
					'Content-Type' => 'x-www-form-urlencoded'
				],
				'body'		=> $parameters
			]);
		}
		else
		{
			$response = GuzzleHttp\get($service->access_token_url,[
				'headers'	=> ['Accept' => 'application/json'],
				'query'		=> $parameters
			]);
		}
	}
	catch (GuzzleHttp\Exception\ClientException $e)
	{
		//print "<pre>"; print_r($e); print "</pre>";
		//print "BODY = ".$e->getBody()."\n";
		throw $e;
	}
	
	$contentType = GuzzleHttp\Message\Request::parseHeader($response, 'Content-Type');
	switch ($contentType[0][0])
	{
		case 'application/json':
			$body = json_decode($response->getBody());
			break;
		case 'text/plain':
			$body = []; parse_str((string)$response->getBody(), $body);
			$body = (object)$body;
			break;
		default:
			print "Unknown Content Type: {$contentType[0][0]}\n";
			print "RESPONSE = ".$response->getBody();
			die();
	}
	
	$token->token = $body->access_token;
	if (isset($body->scope)) $token->scope = $body->scope;
	if (isset($body->expires)) $token->expires = $body->expires;
	
	$token->save();
	
	return new RedirectResponse('/');
});

$app->mount('/oauth2', $oauth2);
