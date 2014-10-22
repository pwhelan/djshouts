<?php

use Silex\Application as App;

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\RedirectResponse;

use google\appengine\api\cloud_storage\CloudStorageTools;


$img = $app['controllers_factory'];


$img->post('/upload', function(Request $request) {
	
	$user = Djshouts\User::
			where('id', '==', $request->getSession()->get('user_id'))
		->first();
	
	
	$upload_url = CloudStorageTools::createUploadUrl(
		'/img/upload',
		[ 'gs_bucket_name' => 'djshouts.appspot.com' ]
	);
	
	if (!$request->files->has('image'))
	{
		return new Response(
			json_encode([
				'image'		=> null,
				'upload_url'	=> $upload_url]
			),
			200,
			['Content-Type' => 'application/json']
		);
	}
	
	
	$uploaded = $request->files->get('image');
	$filename = 'image-'.time().mt_rand(1000000, 100000000);
	
	$attempts = [
		'getClientOriginalExtension',
		'guessClientExtension',
		'getExtension',
		'guessExtension'
	];
	
	$ext = null;
	for ($i = 0; $i < count($attempts) && $ext == null; $i++)
	{
		$ext = $uploaded->{$attempts[$i]}();
	}
	
	switch($ext)
	{
		case 'jpeg':
		case 'png':
		case 'gif':
		case 'jpg':
			break;
		default:
			if (Environment::isAppEngine() && 0)
			{
				throw new Exception('Illegal File Extension: '.$ext);
			}
			$ext = 'png';
			break;
	}
	
	$filename .= ".".$ext;
	
	$file = $uploaded->move('gs://djshouts.appspot.com/', $filename);
	
	
	if (!$request->get('id'))
	{
		$image = new Djshouts\Image;
		$image->user = $user;
	}
	else
	{
		$image = Djshouts\Image::find($request->get('id'));
	}
	
	$image->filename = $file->getPathname();
	$image->save();
	
	
	return new Response(
		json_encode([
			'image'		=> $image->toArray(),
			'upload_url'	=> $upload_url]
		),
		200,
		['Content-Type' => 'application/json']
	);
	
});

$img->get('/', function(App $app, Request $request) {
	
	$user = Djshouts\User::
			where('id', '==', $request->getSession()->get('user_id'))
		->first();
	
	$images = Djshouts\Image::where('user', '==', $user)->get();
	$upload_url = CloudStorageTools::createUploadUrl('/img/upload');
	
	return $app['view']->render('images', [
		'images' => $images,
		'upload_url' => $upload_url
	]);
});

$img->get('/embed/{id}', function(App $app, Request $request, $id) {
	
	$user = Djshouts\User::
			where('id', '==', $request->getSession()->get('user_id'))
		->first();
	
	
	$images = Djshouts\Image::where('user', '==', $user)->get();
	if ($id)
	{
		$image = Djshouts\Image::where('user', '==', $user)
			//->andWhere('id', '==', $id)
		->first();
		if (!$image)
		{
			throw new Exception('Not Found');
		}
	}
	else
	{
		$image = new Djshouts\Image;
	}
	
	$upload_url = CloudStorageTools::createUploadUrl('/img/upload');
	
	return $app['view']->partial('images', [
		'images'	=> $images,
		'upload_url'	=> $upload_url,
		'image'		=> $image
	]);
	
})->value('id', null);

$img->get('/{id}', function(App $app, Request $request, $id) {
	
	$image = Djshouts\Image::find($id);
	return "<img src='{$image->getUrl()}'>"; //new RedirectResponse($image->secure_url);
});

$img->get('/crop/{size}/{id}', function(App $app, Request $request, $size, $id) {
	
	$negotiator   = new \Negotiation\FormatNegotiator();
	$format = $negotiator->getBest(
		$request->attributes->get('_accept')->getValue(), 
		['application/json', 'text/html', 'image/*']
	);
	
	
	$image = Djshouts\Image::find($id);
	$cropped = $image->crop((int)$size);
	
	switch ($format->getValue())
	{
		case 'application/json':
			return new Response(
				json_encode($cropped->toArray()),
				200,
				['Content-Type' => 'application/json']
			);
		default:
			return new RedirectResponse(
				$cropped->url,
				301,
				['X-Image-URL-ID' => $cropped->id]
			);
	}
});

$img->get('/external/{id}', function(App $app, $id) {
	
	$image = Djshouts\Image::find($id);
	return new Response(
		file_get_contents($image->filename),
		200,
		[
			'Content-Type'	=> 'image/jpeg',
			'Expires'	=> date("D, d M Y H:i:s", strtotime("+1 years"))
		]
	);
});

$img->before(function(Request $request) {
	
	$urlparts = array_filter(
		explode("/", $request->getUri()),
		function ($part) {
			return strlen($part) > 0;
		}
	);
	
	if ($urlparts[3] == "img" && $urlparts[4] == "external")
	{
		return null;
	}
	
	if (!$request->getSession()->get('user_id'))
	{
		throw new Exception('Permission Denied');
	}
	
});

$app->mount('/img', $img);
