<?php

namespace Datachore;

abstract class Datastore
{
	protected $_datasetId;
	protected static $_instance;
	
	final public function __construct(array $config = [])
	{
		$this->_datasetId = isset($config['datasetId']) ?
			$config['datasetId'] : $_SERVER['APPLICATION_ID'];
		
		$this->__initialize($config);
		self::$_instance = $this;
	}
	
	public static function getInstance()
	{
		return self::$_instance;
	}
	
	public function getDatasetId()
	{
		return $this->_datasetId;
	}
	
	abstract protected function __initialize(array $config = null);
	abstract public function Factory($type);
	abstract public function isInstanceOf($object, $typeName);
}
