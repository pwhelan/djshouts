<?php

// GAE does not define this by default, wtf?
if (!isset($_SERVER['SERVER_PORT'])) {
	$_SERVER['SERVER_PORT'] = $_SERVER['HTTPS'] == 'off' ? 80 : 443;
}

require_once __DIR__.'/vendor/autoload.php';


class SlimMtHaml extends \Slim\View
{
	private $_haml;
	
	
	public function __construct()
	{
		parent::__construct();
		$this->_haml = new MtHaml\Environment('php');
	}
	
	private function _render($template)
	{
		$executor = new MtHaml\Support\Php\Executor($this->_haml, [
			'cache' => sys_get_temp_dir().'/haml',
		]);
		
		// Compiles and executes the HAML template, with variables given as second
		// argument
		return $executor->render(__DIR__.'/views/'.$template.'.haml', $this->data->all());
	}
		
	public function render($template)
	{
		$this->data->set('content', $this->_render($template));
		return $this->_render('index');
	}
}

class MyLogWriter
{
	public function write($message, $level)
	{
		
	}
}


$app = new \Slim\Slim([
	'view'		=> new SlimMtHaml,
	'log.writer'	=> new MyLogWriter
]);

$con = function() use ($app) {
	$datastore = new Datachore\Datastore\GoogleRemoteApi;
require_once __DIR__.'/public/index.php';
};
$con();



$app->run();
