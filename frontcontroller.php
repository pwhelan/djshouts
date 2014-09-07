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


$app = new Silex\Application;

$app->register(new Silex\Provider\TwigServiceProvider(), [
	'twig.path' => __DIR__.'/views',
]);

class MtHamlWithPhpExecutorServiceProvider extends SilexMtHaml\MtHamlServiceProvider
{
	public function register(Application $app)
	{
		parent::register($app);
		
		$app['mthaml.php'] = $app->share(function ($app) {
			$environment = new MtHaml\Environment('twig', [
				'enable_escaper' => true
			]);
			return new MtHaml\Support\Php\Executor($environment, [
				'cache' => sys_get_temp_dir().'/haml',
			]);
		});
	}
}

$app->register(new MtHamlWithPhpExecutorServiceProvider);

$app['session'] = $app->share(function ($app) {
	return $app['request']->getSession();
});

$app['view'] = $app->share(function(Application $app) {
	
	class MtHamlRenderer
	{
		private $app;
		
		public function __construct(Application $app)
		{
			$this->app = $app;
		}
		
		private function _templateFilePath($template)
		{
			return __DIR__.'/views/'.$template.'.haml';
		}
		
		public function render($template, $data)
		{
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

$init = function() use ($app) {
	$datastore = new Datachore\Datastore\GoogleRemoteApi;
	require_once __DIR__.'/public/index.php';
};
$init();

$app['debug'] = true;


$app->before(function (Request $request) {
	
	$memcache = new Memcache;
	$step = $memcache->get('setup_wizard_step');
	
	if ($step === false)
	{
		$services = Deejaypages\OAuth2\Service::all();
		$is_setup_done = count($services) > 0;
		
		$memcache->set('setup_wizard_step', 0, 0, 0);
	}
	else
	{
		$is_setup_done = ($step >= 2);
	}
	
	if (!$is_setup_done)
	{
		$parts = explode('/', $request->getRequestUri());
		if (count($parts) < 2 || $parts[1] != 'setup')
		{
			return new RedirectResponse('/setup');
		}
	}
	
});

$app->error(function(Exception $e, $code) use ($app) {
	return new Response('Error: '.$e->getMessage());
});

$stack = (new Stack\Builder())
	->push('Stack\Session');

$app = $stack->resolve($app);
Stack\run($app);
