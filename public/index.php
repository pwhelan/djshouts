<?php

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\RedirectResponse;


$app->get('/', function (Application $app) {
	
	//$djs = \Deejaypages\DJ::all();
	/*
	$djs = \Deejaypages\DJ::where(function($q) {
			$q->whereEquals('name', 'Madjester - DJ')
				->andWhereEquals('id', 148003);
			})
		->get();
	
	print "<pre>"; print_r($djs); print "</pre>";
	/*
	$dj = new \Deejaypages\DJ;
	$dj->name = "Mystery Man";
	$dj->picture = 'AMIfv94-lx5g6kkC5fAjCKHOCQRZ5LFSA6AsYVuP-RhukQ8pf-NjNw5CtqOIcHphQCr-950kWTe7n89YG1jQM3IaSxcIPVd8Zkt6GoPB1F3o0YBpHEAjhUNEh-6p4goLzzkpyAdlpL1A25UDQZL_qMFBrnaZo6EMSQ/./bassnight_edited';
	$dj->user_id = 31337;
	$dj->save();
	
	print "<pre>";
	print_r($dj);
	print "</pre>";
	
	$djs = \Deejaypages\DJ::where(function($q) {
			$q->whereEquals('name', 'Madjester - DJ')
				->andWhereEquals('id', 148003);
			})
		->get();
	
	foreach($djs as $dj) {
		if ($dj->id == 148003) {
			$dj->name = 'Madjester - DJ';
			//$dj->picture = 'AMIfv94-lx5g6kkC5fAjCKHOCQRZ5LFSA6AsYVuP-RhukQ8pf-NjNw5CtqOIcHphQCr-950kWTe7n89YG1jQM3IaSxcIPVd8Zkt6GoPB1F3o0YBpHEAjhUNEh-6p4goLzzkpyAdlpL1A25UDQZL_qMFBrnaZo6EMSQ/./bassnight_edited';
			//$dj->user_id = 143003;
			//$dj->save();
			print "SAVING DJ MADJESTER<br/>\n";
		}
	}
	*/
	return $app['']->render('helloworld', ['djs' => $djs]);
	//print "<pre>"; print_r($djs); print "</pre>";
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
	
	$app['mthaml']->render('setup/firstuser', ['is_setup' => true]);
});

$setup->post('/firstuser', function() use ($app) {
	$users = Deejaypages\User::all();
	if (count($users) >= 1)
	{
		$app->error();
		die("NO NO NO!");
	}
	
	$user = new Deejaypages\User;
	foreach($app->request->post() as $key => $val)
	{
		$user->{$key} = $val;
	}
	
	if ($user->save())
	{
		$memcache = new Memcache;
		$memcache->set('setup_wizard_step', 1, 0, 0);
	}
	
	$app->redirect('/setup');
});

$setup->get('/oauth2', function() use ($app) {
	
	$services = Deejaypages\OAuth2\Service::all();
	if (count($services) >= 1)
	{
		$memcache = new Memcache;
		$memcache->set('setup_wizard_step', 2, 0, 0);
		$app->redirect('/');
	}
	
	return $app['view']->render('/setup/oauth2/service', ['is_setup' => true]);
});

$setup->post('/oauth2/(:id)', function($id = 0) use ($app) {
	
	$service = new Deejaypages\OAuth2\Service;
	foreach($app->request->post() as $key => $val)
	{
		$service->{$key} = $val;
	}
	
	if ($service->save())
	{
		$memcache = new Memcache;
		$memcache->set('setup_wizard_step', 2, 0, 0);
	}
	
	return new RedirectResponse('/setup');
});

$app->mount('/setup', $setup);
