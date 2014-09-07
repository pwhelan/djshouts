<?php

use Silex\Application as Application;

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\RedirectResponse;

use Djshouts\OAuth2;

use google\appengine\api\taskqueue\PushTask;


$task = $app['controllers_factory'];
$task->post('/getconnections', function(App $app, Request $request) {
	
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

$app->mount('/task', $task);
