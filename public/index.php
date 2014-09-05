<?php

$app->get('/', function () use ($app) {
	
	
	
	$djs = \Deejaypages\DJ::all();
	//print "<pre>"; print_r($djs); print "</pre>";
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
	$app->render('index', ['djs' => $djs]);
	//print "<pre>"; print_r($djs); print "</pre>";
	
});
