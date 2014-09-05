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
	
	public function render($template)
	{
		$tmplfname = __DIR__.'/views/' . $template . '.haml';
		$tmplcode = file_get_contents($tmplfname);
		
		$compiled = $this->_haml->compileString($tmplcode, $tmplfname);
		
		extract($this->data->all());
		return eval('?>' . $compiled);
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
