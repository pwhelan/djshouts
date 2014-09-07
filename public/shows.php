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


$shows = $app['controllers_factory'];

$shows->get('/golive/{id}', function(App $app, Request $request, $id) {
	
	$user = Djshouts\User
			::where('id', '==', $request->getSession()->get('user_id'))
			->get()
		->first();
	
	$show = Djshouts\Show::where('id', '==', $id)
			//->andWhere('user', '==', $user->key)
		->first();
	
	if (!$show)
	{
		throw new NotFoundHttpException("No such show: ".$id);
	}
	
	$show->is_live = true;
	$show->save();
	
	
	$task = [];
	
	$tasks[] = new PushTask('/task/scrobble',
		['show_id' => $show->id],
		['delay_seconds' => 60]
	);
	
	$tasks[] = new PushTask('/task/publish', ['show_id' => $show->id]);
	
	
	(new PushQueue)->addTasks($tasks);
	
	
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
	
	return $app['view']->render('shows/history', [
		'shows'	=> $shows
	]);
	
});

$create_edit = function(App $app, Request $request, $id = 0) {
	
	$user = Djshouts\User::where('id', '==', $request->getSession()
		->get('user_id'))->get()->first();
	
	$shows = Djshouts\Show::where('user', '==', $user)->get();
	
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
	}
	
	$app['view']->is_shows_page = true;
	
	return $app['view']->render('shows/edit', [
		'user'	=> $user,
		'shows'	=> $shows,
		'urls'	=> $urls,
		'show'	=> $show
	]);
	
};

$shows->get('/create', $create_edit);
$shows->get('/{id}/edit', $create_edit)->value('id', null);

$shows->post('/{id}', function(App $app, Request $request) {
	
	$user = Djshouts\User::where('id', '==', $request->getSession()
		->get('user_id'))->get()->first();
	
	$show = new Djshouts\Show;
	$show->user = $user->key;
	$show->url = $request->get('url');
	$show->title = $request->get('title');
	$show->description = $request->get('description');
	
	$show->save();
	
	return new RedirectResponse("/profile");
	
})->value('id', null);

$shows->get('/{id}', function(App $app, Request $request, $id) {
	
	$show = Djshouts\Show::where('id', '==', $id)->first();
	
	$app['view']->is_shows_page = true;
	
	$app['view']->flashplayer = function($show, $use_https = false) use ($request) {
		
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
		
		return $scheme .'://' .$request->getHost() .
			($standard ? '' : ':' . $request->getPort()) .
			'/media/ffmp3-tiny.swf?' .
			http_build_query([
				'url'		=> $show->url,
				'title'		=> $show->title,
				'tracking'	=> 'false',
				'jsevents'	=> 'false'
			]);
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
