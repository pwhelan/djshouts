<?php

use Silex\Application as App;

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\RedirectResponse;

use Djshouts\OAuth2;

use google\appengine\api\taskqueue\PushTask;
use google\appengine\api\taskqueue\PushQueue;
use google\appengine\TaskQueueAddRequest\RequestMethod as PushTaskRequestMethod;


$task = $app['controllers_factory'];
$task->post('/getconnections', function(App $app, Request $request) {
	
	$token_id = $request->get('token_id');
	$token = OAuth2\Token::where('id', '==', $token_id)->get()->first();
	$connections = new Datachore\Collection;
	$tasks = [];
	
	
	$urls = [
		'person'	=> 'https://graph.facebook.com/v1.0/me',
		'page'		=> 'https://graph.facebook.com/v1.0/me/accounts',
		'group'		=> 'https://graph.facebook.com/v2.1/me/groups'
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
				->first();
			
			
			if (count($connection) <= 0)
			{
				print "New Connection[{$type}]: {$entity->name}\n";
				$connection = new OAuth2\Connection;
				$connection->user = $token->user;
				$connection->service = $token->service;
				$connection->name = $entity->name;
				$connection->xid = $entity->id;
				$connection->type = $type;
				$connection->is_hidden = false;
				if ($type == "page") $connection->token = $entity->token;
				$connection->icon_url = $entity->icon;
				
				
				switch ($type)
				{
					case 'person':
						$connection->precedence = 50;
						break;
					case 'page':
						$connection->precedence = 10;
						break;
					case 'group':
						$connection->precedence = 1;
						break;
				}
				
				$connections[] = $connection;
				$connection->save();
			}
			else
			{
				print "Already exist: {$entity->name}:{$entity->id}\n";
				switch ($type)
				{
					case 'person':
						$connection->precedence = 50;
						break;
					case 'page':
						$connection->precedence = 10;
						break;
					case 'group':
						$connection->precedence = 1;
						break;
				}
				$connection->is_hidden = false;
				$connection->save();
			}
			
			if ($type == 'group' || $type == 'page')
			{
				$app['monolog']->addError("Start Precedence for {$connection->xid}:{$connection->id}");
				
				$tasks[] = new PushTask(
					'/task/getprecedence',
					['connection_id' => (int)$connection->id]
				);
			}
		}
	}
	
	(new PushQueue('scraper'))->addTasks($tasks);
	
	// Error: operating on too many entity groups in a single transaction.
	//$connections->save();
	
	return new Response('Created '.count($connections).' Connections');
});


$task->post('/getprecedence', function(App $app, Request $request) {
	
	$connection_id = $request->get('connection_id');
	if (!$connection_id)
	{
		$app['monolog']->addError('No Connection ID');
		return new Response("");
	}
	
	$connection = OAuth2\Connection::find($connection_id);
	if (!$connection)
	{
		$app['monolog']->addError('Unknown Connection: ' . $connection_id);
		return new Response("");
	}
	
	
	$me = OAuth2\Connection::where('user', '==', $connection->user)
			->andWhere('type', '==', 'person')
		->first();
	if (!$me)
	{
		$app['monolog']->addError("Unable to find personal connection: {{$connection->user->id}}");
		return new Response("");
	}
	
	
	$token = OAuth2\Token::where('user', '==', $connection->user)
			->andWhere('service', '==', $connection->service)
		->first();
	
	if ($request->get('next'))
	{
		$url = $request->get('next');
		$url = parse_url($next);
		
		$query = [];
		parse_str($url['query'], $query);
		$url['query'] = (object)$query;
		
		if (isset($url['query']->since))
		{
			if ($url['query']->since < strtotime("6 months ago"))
			{
				$app['monolog']->addInfo("Halting pagination at ".date("Y-m-d", $url['query']->since));
				return new Response("Done");
			}
			else
			{
				$app['monolog']->addInfo("Continuing pagination until ".date("Y-m-d", $url['query']->since));
			}
		}
		else
		{
			$app['monolog']->addInfo("PAGINATION URL = ".print_r($url, true));
		}
	}
	else
	{
		$url = "https://graph.facebook.com/v2.1/{$connection->xid}/feed";
	}
	
	
	$response = GuzzleHttp\get($url, ['query' => ['access_token' => $token->token]]);
	
	$feed = json_decode($response->getBody());
	$count = 0;
	
	foreach ($feed->data as $post)
	{
		if ($post->from->id == $me->xid)
		{
			$count++;
		}
	}
	
	
	$connection->precedence += $count;
	$connection->save();
	
	if (isset($feed->paging) && isset($feed->paging->prev))
	{
		$app['monolog']->addInfo("Paged Request for {$connection->xid}:{$connection->id} to {$feed->paging->prev}");
		
		(new PushTask('/task/getprecedence', [
			'connection_id'	=> $connection->id,
			// go back in time!
			'next'		=> $feed->paging->prev,
			'delay_seconds'	=> 5
		]))->add('scraper');
	}
	
	
	return new Response(json_encode($connection->toArray()), 200, ['Content-Type' => 'application/json']);
});

$task->post('/goliveanyways', function(Request $request) {
	
	$show_id = $request->get('show_id');
	$show = Djshouts\Show::where('id', '==', $show_id)->first();
	
	
	if (!$show->is_live)
	{
		(new PushTask('/shows/golive/'.$show->id, 
			['base_url'	=> $request->get('base_url')],
			['method'	=> 'GET']
		))->add();
	}
	
	return "Done";
});

$task->post('/scrobble', function(Request $request) {
	
	$show_id = $request->get('show_id');
	$show = Djshouts\Show::where('id', '==', $show_id)->first();
	
	// http://198.154.106.102:8567/admin/listclients?mount=/live
	//	<icestats>
	//		<source mount="/live">
	//		<listeners>5</listeners>
	//		<listener id="272263">
	//			<IP>82.9.182.13</IP>
	//			<UserAgent>BASS/2.4</UserAgent>
	//			<lag>0</lag>
	//			<Connected>31502</Connected>
	//		</listener>
	//		<listener id="272319">
	//			<IP>81.151.118.117</IP>
	//			<UserAgent>RMA/1.0 (compatible; RealMedia)</UserAgent>
	//			<lag>0</lag>
	//			<Connected>31377</Connected>
	//		</listener>
	//		<listener id="274704">
	//			<IP>50.7.96.138</IP>
	//			<UserAgent>Icecast 2.3.3-kh9</UserAgent>
	//			<lag>0</lag>
	//			<Connected>25906</Connected>
	//		</listener>
	//		<listener id="279627">
	//			<IP>62.131.207.131</IP>
	//			<UserAgent>WinampMPEG/5.52</UserAgent>
	//			<lag>0</lag>
	//			<Connected>9325</Connected>
	//		</listener>
	//		<listener id="283752">
	//			<IP>83.137.254.40</IP>
	//			<UserAgent>
	//			Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0
	//			</UserAgent>
	//			<lag>0</lag>
	//			<Connected>265</Connected>
	//		</listener>
	//		</source>
	//	</icestats>
	
	$response = GuzzleHttp\get('http://198.154.106.102:8567/admin/stats', [
		'auth' => ['admin', 'ReN@g@De2012']
	]);
	
	$xml = (string)$response->getBody();
	$result = simplexml_load_string($xml);
	
	foreach ($result->source as $source)
	{
		if ((int)$source->listeners > 0)
		{
			break;
		}
	}
	
	
	$stat = new Djshouts\Radio\Stat;
	$stat->show = $show->key;
	$stat->timestamp = new DateTime; //(new DateTime)->format("Y-m-d\TH:i:s.u\Z");
	$stat->listeners = $result->source[1]->listeners;
	$stat->title = $source->title;
	$stat->description = $result->source[1]->server_description;
	$stat->save();
	
	
	$source_ip = (string)$result->source[1]->source_ip;
	if ($show->source_ip)
	{
		if ($show->source_ip == $source_ip)
		{
			(new PushTask('/task/scrobble',
				['show_id' => $show->id],
				['delay_seconds' => 60]
			))->add();
		}
	}
	else
	{
		$show->source_ip = (string)$result->source[1]->source_ip;
		$show->is_live = true;
		$show->save();
		
		(new PushTask('/task/scrobble',
			['show_id' => $show->id],
			['delay_seconds' => 60]
		))->add();
	}
	
	return json_encode($stat->toArray());
});

// Key('Djshouts_User', 5313752060657664)
// Key('Djshouts_Image_URL', 5906335677808640)

$task->post('/publish', function(App $app, Request $request) {
	
	$show_id = $request->get('show_id');
	$connection_id = $request->get('connection_id');
	$base_url = $request->get('base_url');
	
	
	$app['monolog']->addInfo('Vars: '.implode(", ", array_keys((array)$request->request->all())));
	$app['monolog']->addInfo('Values: '.implode(", ", array_values((array)$request->request->all())));
	$app['monolog']->addInfo('Find Connection: '.$connection_id);
	
	$connection = Djshouts\OAuth2\Connection::find($connection_id);
	if (!$connection)
	{
		// Log error, move on!
		return new Response('No Social Connection');
	}
	
	$app['monolog']->addInfo('Have Connection!');
	
	// Only have support to publish to facebook for now
	$service = OAuth2\Service::where('id', '==', $connection->service)->first();
	if (!$service)
	{
		// Log error, move on!
		return new Response('No Facebook');
	}
	
	$app['monolog']->addInfo('Have Service!');
	
	
	$show = Djshouts\Show::where('id', '==', $show_id)->first();
	$app['monolog']->addInfo('Have Show!');
	
	$token = OAuth2\Token::where('user', '==', $show->user->key)
			->andWhere('service', '==', $service->key)
		->first();
	
	if (!$token)
	{
		// Log error, move on!
		return new Response('No Facebook Token');
	}
	
	
	$message = [
		'name'		=> $show->title,
		'message'	=> $show->description,
		'link'		=> 'http://' . $base_url . '/shows/' . $show->id,
		'picture'	=> 'http://' . $base_url . '/img/external/' . $show->image->parent->id,
		'type'		=> 'video',
		'source'	=> 'https://' . $base_url . '/media/ffmp3-tiny.swf?' .
			http_build_query([
				'url'		=> $show->url,
				'title'		=> $show->title,
				'tracking'	=> 'false',
				'jsevents'	=> 'false'
			]),
		'caption'	=>  $show->title,
		'access_token'	=> $token->token
	];
	
	try 
	{
		$response = GuzzleHttp\post('https://graph.facebook.com/' . $connection->xid . '/feed', [
			'query'		=> ['access_token' => $token->token],
			'body'		=> $message
		]);
	}
	catch (Exception $e)
	{
		$app['monolog']->addInfo("HTTP Error: ".$e->getResponse());
		throw $e;
	}
	
	return $response->getBody();
});

$app->mount('/task', $task);
