<?php

namespace Datachore;

class DatastoreProtobufRequestWrapper
{
	private $_proxied;
	
	
	public function __construct($proxied)
	{
		$this->_proxied = $proxied;
	}
	
	public function __get($key)
	{
		return $this->_proxied->$key;
	}
	
	public function __set($key, $val)
	{
		return $this->_proxied->$key = $val;
	}
	
	public function __call($func, $args)
	{
		if ($func == 'serializeToString')
		{
			$func = 'serialize';
		}
		else if ($func == 'parseFromString')
		{
			$func = 'parse';
		}
		
		return call_user_func_array([$this->_proxied, $func], $args);
	}
}

class DatastoreProtobufWrapper extends Datastore
{
	public function call()
	{
		$args = func_get_args();
		$call = $args[0];
		
		return call_user_func_array([$this, 'call'], $args);
	}
	
	private function _callMethod($methodName, $request, $response)
	{
		\google\appengine\runtime\ApiProxy::makeSyncCall(
			'datastore_v4',
			ucfirst($methodName),
			$request, //new DatastoreProtobufRequestWrapper($request),
			$response
		);
		
		return $response;
	}
	
	public function __call($func, $args)
	{
		$responseClass = str_replace('Request', 'Response', get_class($args[1]));
		$response = new $responseClass;
		
		return $this->_callMethod($func, $args[1], $response);
	}
	
	private function _getBaseUrl()
	{
		return '/datastore/v1beta1/datasets';
	}
	
	private function _getFullBaseUrl()
	{
		return rtrim($this->_host, '/') . '/' . ltrim($this->_getBaseUrl(), '/');
	}
	
	private function _getUrlForMethod($methodName)
	{
		return $this->_getFullBaseUrl() . '/' . $this->_dataset . '/' . $methodName;
	}
}

class Datastore {
	static $scopes = [
		"https://www.googleapis.com/auth/datastore",
		"https://www.googleapis.com/auth/userinfo.email",
	];
	
	
	public function __construct($config = null)
	{
		if (0):
			$this->__client = new \Google_Client;
			$this->__client->setApplicationName($config['application-id']);
			$this->__client->setClientId($config['client-id']);
			$this->__client->setAssertionCredentials(
				new \Google_Auth_AssertionCredentials(
					$config['service-account-name'],
					self::$scopes,
					$config['private-key']
				)
			);
			
			$this->__service = new \Google_Service_Datastore($this->__client);
		endif;
	}
	
	public function getDatasets()
	{
		if (0) return $this->__service->datasets;
		return new DatastoreProtobufWrapper;
	}
	
	public function Factory($type)
	{
		if (0):
			$className = 'Google_Service_Datastore_'.$type;
			return new $className;
		endif;
		
		//$className = 'api\\services\\datastore\\'.$type;
		$className = 'google\\appengine\\datastore\\v4\\'.$type;
		return new $className;
	}
	
	public function isInstanceOf($object, $typeName)
	{
		if (0):
			return get_class($object) == 'Google_Service_Datastore_'.$typeName;
		endif;
		
		//return get_class($object) == 'api\\services\\datastore\\'.$typeName;
		return get_class($objeect) == 'google\\appengine\\datastore\\v4\\'.$typeName;
	}
}
