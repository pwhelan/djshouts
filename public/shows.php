<?php

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;

use Silex\Application as App;

use google\appengine\api\cloud_storage\CloudStorageTools;
use google\appengine\api\taskqueue\PushTask;
use google\appengine\api\taskqueue\PushQueue;

use Djshouts\OAuth2;


function flashvars($request, $show, $autoplay = false)
{
	$use_https = ($_SERVER['HTTPS'] == 'on');
	
	if ($request->getPort() == 80 || $request->getPort() == 443)
	{
		$standard = true;
		$scheme = $use_https ? 'https' : 'http';
	}
	else
	{
		$standard = false;
		$scheme = 'http';
	}
	
	$base_url = $scheme .'://' .$request->getHost() .
		($standard ? '' : ':' . $request->getPort());
	
	return [
		'url'		=> $base_url. '/shows/'. $show->id . '/stream.mp3#',
		//'url'		=> $show->url,
		'title'		=> $show->title,
		'tracking'	=> 'false',
		'jsevents'	=> 'false',
		'autoplay'	=> $autoplay ? 'true' : 'false'
	];
};

function flashplayer($request, $show, $autoplay = false, $use_https = -1)
{
	if ($use_https !== -1)
	{
		$scheme = $use_https ? 'https' : 'http';
		$standard = ($request->getPort() == 80 || $request->getPort() == 443);
	}
	else if ($request->getPort() == 80 || $request->getPort() == 443)
	{
		$use_https = ($_SERVER['HTTPS'] == 'on');
		$standard = true;
		$scheme = $use_https ? 'https' : 'http';
	}
	else
	{
		$use_https = ($_SERVER['HTTPS'] == 'on');
		$standard = false;
		$scheme = $use_https ? 'https' : 'http';
	}
	
	$base_url = $scheme .'://' .$request->getHost() .
		($standard ? '' : ':' . $request->getPort());
	
	return $base_url.
		'/media/ffmp3-tiny.swf?' .
		http_build_query(flashvars($request, $show, $autoplay));
};

$shows = $app['controllers_factory'];

$shows->get('/{id}/stream.mp3', function($id) {
	
	$show = Djshouts\Show::find($id);
	return new RedirectResponse($show->url);
});

$shows->get('/golive/{id}', function(App $app, Request $request, $id) {
	
	$show = Djshouts\Show::where('id', '==', $id)
			//->andWhere('user', '==', $user->key)
		->first();
	
	if (!$show)
	{
		throw new NotFoundHttpException("No such show: ".$id);
	}
	
	if (!$show->is_live)
	{
		$show->is_live = true;
		$show->save();
		
		
		$task = [];
		
		$tasks[] = new PushTask('/task/scrobble',
			['show_id' => $show->id],
			['delay_seconds' => 60]
		);
		
		
		foreach ($show->connections as $connection)
		{
			$tasks[] = new PushTask('/task/publish', [
				'base_url'	=> $request->get('base_url') ?
					$request->get('base_url') :
					$request->getHost() . ':' .$request->getPort(),
				'show_id'	=> $show->id,
				'connection_id'	=> $connection->getKeyValue()->getPathElement(0)->getId()
			],['delay_seconds' => 60]);
		}
		
		(new PushQueue)->addTasks($tasks);
	}
	
	return new Response(
		json_encode($show->toArray()),
		200,
		['Content-Type' => 'application/json']
	);
});

$shows->get('/history', function(App $app, Request $request) {
	
	$user = Djshouts\User::where('id', '==', $request->getSession()
		->get('user_id'))->get()->first();
	
	$shows = Djshouts\Show::where('user', '==', $user)->get();
	
	
	$app['view']->is_shows_page = true;
	
	$app['view']->flashplayer = function($show, $autoplay = false, $use_https = false) use ($request)
	{
		return flashplayer($request, $show, $autoplay, $use_https);
	};
	
	$app['view']->flashvars = function($show, $use_https = false) use ($request)
	{
		return flashvars($request, $show, $use_https);
	};
	
	
	return $app['view']->render('shows/history', [
		'shows'	=> $shows
	]);
	
});

$create_edit = function(App $app, Request $request, $id = 0) {
	
	$user = Djshouts\User::where('id', '==', $request->getSession()
		->get('user_id'))->get()->first();
	
	$shows = Djshouts\Show::where('user', '==', $user)->get();
	$connections = OAuth2\Connection::where('user', '==', $user)
			->andWhere('is_hidden', '==', false)
			->orderBy('precedence', 'desc')
			// Temporary fix...
			->limit(100)
		->get();
	
	
	$urls = $shows->map(
		function($show) {
			return $show->url;
		}
	)->toArray();
	
	
	if ($id)
	{
		$show = Djshouts\Show::where('id', '==', $id)->first();
	}
	else
	{
		$show = new Djshouts\Show;
		
		$DJ = Djshouts\DJ::where('user', '==', $user)->first();
		if ($DJ)
		{
			$image = $DJ->image;
		}
		else
		{
			$image = Djshouts\Image::where('user', '==', $user)->first();
		}
		if ($image)
		{
			$show->image = $image->crop(320);
		}
		
	}
	
	
	$app['view']->is_shows_page = true;
	
	return $app['view']->render('shows/edit', [
		'user'		=> $user,
		'shows'		=> $shows,
		'urls'		=> $urls,
		'show'		=> $show,
		'connections'	=> $connections
	]);
	
};

$shows->get('/create', $create_edit);
$shows->get('/{id}/edit', $create_edit)->value('id', null);

$shows->post('/{id}', function(App $app, Request $request) {
	
	$user = Djshouts\User::where('id', '==', $request->getSession()
		->get('user_id'))->get()->first();
	
	if (!$user)
	{
		throw new Exception("Permission Denied");
	}
	
	$show = new Djshouts\Show;
	$show->user = $user->key;
	$show->url = $request->get('url');
	$show->title = $request->get('title');
	$show->description = $request->get('description');
	$show->image = Djshouts\Image\URL::find($request->get('image'));
	$show->is_live = false;
	
	
	foreach ($request->get('connection_ids') as $connection_id)
	{
		$connection = Djshouts\OAuth2\Connection
				::where('id', '==', $connection_id)
				->andWhere('user', '==', $user)
			->first();
		
		if (!$connection)
		{
			continue;
		}
		
		$show->connections[] = $connection;
	}
	
	$show->save();
	
	(new PushTask('/task/goliveanyways',
		['show_id' => $show->id],
		['delay_seconds' => 360]
	))
	->add();
	
	return new RedirectResponse("/profile");
	
})->value('id', null);

$shows->get('/{id}', function(App $app, Request $request, $id) {
	
	$show = Djshouts\Show::where('id', '==', $id)->first();
	
	
	$app['view']->is_shows_page = true;
	$app['view']->flashplayer = function($show, $autoplay = false, $use_https = false) use ($request)
	{
		return flashplayer($request, $show, $autoplay, $use_https);
	};
	$app['view']->flashvars = function($show, $use_https = false) use ($request)
	{
		return flashvars($request, $show, $use_https);
	};
	$app['view']->showurl = function($show) {
		return	($_SERVER['HTTPS'] == "on" ? 'https' : 'http'). '://' .
		 	$_SERVER['HTTP_HOST'] .
			($_SERVER['HTTPS'] == "on" && $_SERVER['SERVER_PORT'] == 443 || 
				$_SERVER['HTTPS'] == "off" && $_SERVER['SERVER_PORT'] == 80 ?
				'' : ':' . $_SERVER['SERVER_PORT']
			)
			.'/shows/'. $show->id;
	};
	
	$app['view']->opengraph = $app['view']
		->partial('shows/opengraph', ['show' => $show]);
	
	return $app['view']->render('shows/show', ['show' => $show]);
});

/*
$shows->before(function(Request $request) {
	
	if (!$request->getSession()->get('user_id'))
	{
		return new RedirectResponse('/');
	}
});
*/

$app->mount('/shows', $shows);
