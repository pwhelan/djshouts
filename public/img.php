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
	
	$uploaded = $request->files->get('image');
	
	$filename = 'image-'.time().mt_rand(1000000, 100000000);
	
	$attempts = [
		'getExtension',
		'guessExtension',
		'guessClientExtension',
		'getClientOriginalExtension'
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
			throw new Exception('Illegal File Extension: '.$ext);
	}
	
	$filename .= ".".$ext;
	$file = $uploaded->move('gs://djshouts.appspot.com/', $filename);
	
	
	if (!$request->get('id'))
	{
		$image = new Djshouts\Image;
	}
	else
	{
		$image = Djshouts\Image::find($request->get('id'));
	}
	
	$image->filename = $file->getPathname();
	$image->save();
	
	$upload_url = CloudStorageTools::createUploadUrl(
		'/img/upload',
		[ 'gs_bucket_name' => 'djshouts.appspot.com' ]
	);
	
	return new Response(
		json_encode([
			'image' => $image->toArray(),
			'upload_url' => $upload_url]
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

$img->get('/crop/{size}/{id}', function(App $app, Request $request, $size, $id) {
	
	print "<pre>";
	$image = Djshouts\Image::find($id);
	$cropped = $image->crop($size);
	
	return new RedirectResponse($cropped->url);
});

$img->before(function(Request $request) {
	
	if (!$request->getSession()->get('user_id'))
	{
		throw new Exception('Permission Denied');
	}
	
});

$app->mount('/img', $img);
