<?php

use Silex\Application;

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\RedirectResponse;

use google\appengine\api\taskqueue\PushTask;

use Djshouts\OAuth2;


$task = $app['controllers_factory'];
$task->post('/getconnections', function(Application $app, Request $request) {
	
	$token_id = $request->get('token_id');
	$token = OAuth2\Token::where('id', '==', $token_id)->get()->first();
	$connections = new Datachore\Collection;
	
	
	$urls = [
		'person'	=> 'https://graph.facebook.com/v1.0/me',
		'group'		=> 'https://graph.facebook.com/v1.0/me/groups',
		'page'		=> 'https://graph.facebook.com/v1.0/me/accounts'
	];
	
	foreach ($urls as $type => $url)
	{
		try {
			$response = GuzzleHttp\get($url, [
				'query'	=> ['access_token' => $token->token]
			]);
		}
		catch (Exception $e)
		{
			print "ERROR ($type): ".$url."\n";
		}
		
		$entities = json_decode($response->getBody());
		
		if ($type == 'person')
		{
			$entities = [$entities];
		}
		else
		{
			$entities = $entities->data;
		}
		
		foreach ($entities as $entity)
		{
			$connection = OAuth2\Connection::where('xid', '==', $entity->id)
				->andWhere('service', '==', $token->service)
				->andWhere('user', '==', $token->user)
				->andWhere('type', '==', $type)
				->get();
			
			if (count($connection) > 0)
			{
				print "Already exist: {$entity->name}:{$entity->id}\n";
				continue;
			}
			
			$connection = new OAuth2\Connection;
			$connection->user = $token->user;
			$connection->service = $token->service;
			$connection->name = $entity->name;
			$connection->xid = $entity->id;
			$connection->type = $type;
			
			$connections[] = $connection;
			$connection->save();
		}
	}
	
	// Error: operating on too many entity groups in a single transaction.
	//$connections->save();
	
	return new Response('Created '.count($connections).' Connections');
});

$app->mount('/task', $task);
