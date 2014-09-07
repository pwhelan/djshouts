<?php


use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\RedirectResponse;

use Silex\Application;

use google\appengine\api\cloud_storage\CloudStorageTools;

use Djshouts\OAuth2;

use google\appengine\api\taskqueue\PushTask;
use google\appengine\api\taskqueue\PushQueue;


$oauth2 = $app['controllers_factory'];

$oauth2->get('/callback/{servicename}', function(Request $request, $servicename) {
	
	$session = $request->getSession();
	
	$user = Djshouts\User::where('id', '==', $session->get('user_id'))->get()->first();
	if (!$user)
	{
		$user = new Djshouts\User;
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
	
	
	$tasks = [
		new PushTask('/task/getconnections', ['token_id' => $token->id])
	];
	
	$queue = new PushQueue();
	$queue->addTasks($tasks);
	
	return new RedirectResponse('/');
});

$app->mount('/oauth2', $oauth2);
