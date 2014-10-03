<?php

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpKernel\HttpKernelInterface;
use Symfony\Component\HttpFoundation\Session\Storage\Handler\MemcacheSessionHandler;

use Whoops\Provider\Silex\WhoopsServiceProvider;
use Silex\Application;


// GAE does not define this by default, wtf?
if (!isset($_SERVER['SERVER_PORT'])) {
	$_SERVER['SERVER_PORT'] = $_SERVER['HTTPS'] == 'off' ? 80 : 443;
}

if (isset($_SERVER['HTTP_AUTHORIZATION']))
{
	$basic = base64_decode(substr($_SERVER['HTTP_AUTHORIZATION'], strlen('Basic ')));
	$_SERVER['PHP_AUTH_USER'] = explode(':', $basic)[0];
	$_SERVER['PHP_AUTH_PW'] = explode(':', $basic)[1];
}

require_once __DIR__.'/vendor/autoload.php';


class Environment
{
	private static $is_app_engine = null;
	const GAE_APP_ID = 'Google App Engine';
	
	
	// This function is made necessary by the following problems:
	//   * GCS cannot agree on when which URL; public or image serving works,
	//     one works locally the other one @Google... And worse, some work
	//     but only as downloads, some combinations work perfectly others
	//     flat out do not respond.
	public static function isAppEngine()
	{
		if (self::$is_app_engine === null)
		{
			self::$is_app_engine = 
				substr($_SERVER['SERVER_SOFTWARE'], 0, strlen(self::GAE_APP_ID)) == self::GAE_APP_ID;
		}
		
		return self::$is_app_engine;
	}
}

global $app;
$app = new Application;


if (Environment::isAppEngine())
{
	$app->register(new Silex\Provider\MonologServiceProvider(), 
		['monolog.handler' => new Monolog\Handler\SyslogHandler('djshouts')]
	);
}
else
{
	$app->register(new Silex\Provider\MonologServiceProvider(), 
		['monolog.logfile' => __DIR__.'/logs/silex.log']
	);
}


$app->register(new Silex\Provider\TwigServiceProvider());

class MtHamlWithPhpExecutorServiceProvider extends SilexMtHaml\MtHamlServiceProvider
{
	public function register(Application $app)
	{
		parent::register($app);
		
		$app['mthaml.php'] = $app->share(function ($app) {
			$environment = new MtHaml\Environment('php', [
				'enable_escaper'=> true,
				'escape_attrs'	=> false
			]);
			return new MtHaml\Support\Php\Executor($environment, [
				'cache' => './cache/haml'
			]);
		});
		
	}
}

$app->register(new MtHamlWithPhpExecutorServiceProvider);


$app['session'] = $app->share(function ($app) {
	return $app['request']->getSession();
});


$app['view'] = $app->share(function(Application $app) {
	
	class MtHamlRenderer extends ArrayObject
	{
		private $app;
		
		
		public function __set($key, $val)
		{
			return $this->offsetSet($key, $val);
		}
		
		public function __get($key)
		{
			return $this->offsetGet($key);
		}
		
		public function __isset($key)
		{
			return $this->offsetExists($key);
		}
		
		public function __construct(Application $app)
		{
			parent::__construct([], ArrayObject::STD_PROP_LIST);
			$this->app = $app;
		}
		
		private function _templateFilePath($template)
		{
			return preg_replace('/[\/]+/', '/', './views/'.$template.'.haml');
		}
		
		public function render($template, $data)
		{
			$data['content'] = $this->partial($template, $data);
			return $this->partial('index', $data);
		}
		
		public function display($template, $data)
		{
			print $this->render($template, $data);
		}
		
		public function partial($template, $data)
		{
			$data['subrequest'] = function($url) 
			{
				$request = $this->app['request'];
				$subRequest = Request::create($url, 'GET', [], $request->cookies->all(), [], $request->server->all());
				if ($request->getSession()) {
					$subRequest->setSession($request->getSession());
				}
				
				$response = $this->app->handle($subRequest, HttpKernelInterface::SUB_REQUEST, false);
				if (!$response->isSuccessful()) {
					die("WTF {$url} =".$response->getStatusCode());
				}
				return (string)$response->getContent();
			};
			
			foreach ($this as $key => $value)
			{
				$data[$key] = $value;
			}
			
			return $this->app['mthaml.php']->render(
				$this->_templateFilePath($template),
				$data
			);
		}
	}
	
	return new MtHamlRenderer($app);
});


$app['debug'] = file_exists(".git");

if ($app['debug'])
{
	$app->register(new WhoopsServiceProvider);
}

$init = function() use ($app) {
	
	$datastore = new Datachore\Datastore\GoogleRemoteApi;
	
	
	$parts = array_filter(
		explode('/', $_SERVER['REQUEST_URI']),
		function ($part) {
			return $part;
		}
	);
	
	require_once __DIR__.'/public/img.php';
	for ($i = count($parts); $i > 0; $i-- )
	{
		$file = __DIR__.'/public/' .
			implode('/', array_slice($parts, 0, $i)) .
			'.php';
		
		if (file_exists($file))
		{
			require_once $file;
			return;
		}
	}
	
	require_once __DIR__.'/public/index.php';
};
$init();


$app->before(function (Request $request) use ($app) {
	
	$memcache = new Memcache;
	$step = $memcache->get('setup_wizard_step');
	
	if ($step === false)
	{
		$step = 0;
		
		$users = Djshouts\User::all();
		if (count($users) > 0)
		{
			$step = 1;
		}
		$services = Djshouts\OAuth2\Service::all();
		if (count($services) > 0)
		{
			$step = 2;
		}
		
		$memcache->set('setup_wizard_step', $step, 0, 0);
	}
	
	$is_setup_done = ($step >= 2);
	
	
	if (!$is_setup_done)
	{
		$parts = explode('/', $request->getRequestUri());
		if (count($parts) < 2 || $parts[1] != 'setup')
		{
			return new RedirectResponse('/setup');
		}
	}
	
	if ($request->getSession()->get('user_id'))
	{
		$app['view']->is_logged_in = true;
	}
});

//$app->error(function(Exception $e, $code) use ($app) {
//	return new Response('Error: '.$e->getMessage());
//});

$stack = (new Stack\Builder())
	->push('Stack\Session', [
		'session.storage.handler' => $app->share(function() {
			return new MemcacheSessionHandler(new \Memcache);
		})
	])
	->push('Negotiation\Stack\Negotiation');

$stack = $stack->resolve($app);
Stack\run($stack);
