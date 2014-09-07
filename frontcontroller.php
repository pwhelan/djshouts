<?php

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\RedirectResponse;

use Silex\Application;


// GAE does not define this by default, wtf?
if (!isset($_SERVER['SERVER_PORT'])) {
	$_SERVER['SERVER_PORT'] = $_SERVER['HTTPS'] == 'off' ? 80 : 443;
}

require_once __DIR__.'/vendor/autoload.php';


$app = new Application;


$app->register(new Silex\Provider\TwigServiceProvider());

class MtHamlWithPhpExecutorServiceProvider extends SilexMtHaml\MtHamlServiceProvider
{
	public function register(Application $app)
	{
		parent::register($app);
		
		$app['mthaml.php'] = $app->share(function ($app) {
			$environment = new MtHaml\Environment('php', [
				'enable_escaper' => true
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
			foreach ($this as $key => $value)
			{
				$data[$key] = $value;
			}
			
			$data['content'] = $this->app['mthaml.php']->render(
				$this->_templateFilePath($template),
				$data
			);
			
			return $this->app['mthaml.php']->render(
				$this->_templateFilePath('index'),
				$data
			);
		}
		
		public function display($tempate, $data)
		{
			foreach ($this as $key => $value)
			{
				$data[$key] = $value;
			}
			
			$data['content'] = $this->app['mthaml.php']->render(
				$this->_templateFilePath($template),
				$data
			);
			
			return $this->app['mthaml.php']->display(
				$this->_templateFilePath('index'),
				$data
			);
		}
	}
	
	return new MtHamlRenderer($app);
});


$app['debug'] = true;


$init = function() use ($app) {
	
	$datastore = new Datachore\Datastore\GoogleRemoteApi;
	
	
	$parts = array_filter(
		explode('/', $_SERVER['REQUEST_URI']),
		function ($part) {
			return $part;
		}
	);
	
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
	->push('Stack\Session');

$app = $stack->resolve($app);
Stack\run($app);
